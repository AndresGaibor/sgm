"""Preparación segura de subconsultas independientes usadas por IN en el anillo B."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from heapq import heappop, heappush

from sqlglot import exp

from sgm.ir.models import Operator, Plan
from sgm.migrar import semantica

Evaluar = Callable[[exp.Expression, dict], object]
Filtrar = Callable[[list[dict], str, dict | None], list[dict]]
Columna = Callable[[dict, str], object]
Nombres = Callable[[Operator], list[str]]
Parsear = Callable[[str], exp.Expression]


class SubconsultaNoSoportada(ValueError):
    """Forma de subconsulta para la que el anillo B no tiene equivalencia demostrada."""


def _lista_inicial(expresion: exp.Expression):
    """Busca los IN de esta expresión sin entrar a la SELECT de otro IN."""
    if isinstance(expresion, exp.In) and expresion.args.get("query") is not None:
        yield expresion
        yield from _lista_inicial(expresion.this)
        for opcion in expresion.expressions:
            yield from _lista_inicial(opcion)
        return
    for hija in expresion.iter_expressions():
        yield from _lista_inicial(hija)


def _valores(
    consulta: exp.Expression,
    tablas: dict[str, list[dict]],
    *,
    filtrar: Filtrar,
    evaluar: Evaluar,
    columna: Columna,
) -> list[object]:
    select = consulta.this if isinstance(consulta, exp.Subquery) else consulta
    if not isinstance(select, exp.Select):
        raise SubconsultaNoSoportada("la consulta IN debe ser un SELECT")

    if select.find(exp.In) and any(
        isinstance(nodo, exp.In) and nodo.args.get("query") is not None
        for nodo in select.find_all(exp.In)
    ):
        raise SubconsultaNoSoportada("subconsulta anidada no soportada")

    clausulas_no_soportadas = (
        "distinct",
        "group",
        "having",
        "order",
        "limit",
        "offset",
        "qualify",
        "with",
        "windows",
    )
    if select.args.get("joins"):
        raise SubconsultaNoSoportada("IN requiere una sola fuente de tabla")
    if any(select.args.get(nombre) is not None for nombre in clausulas_no_soportadas):
        raise SubconsultaNoSoportada("cláusula de subconsulta no soportada")

    proyeccion = select.expressions
    if len(proyeccion) != 1:
        raise SubconsultaNoSoportada("IN requiere una sola columna proyectada")
    proyectada = proyeccion[0]
    if not isinstance(proyectada, exp.Column):
        raise SubconsultaNoSoportada(
            "proyección de subconsulta no soportada; requiere una columna simple"
        )

    desde = select.args.get("from_")
    fuente = desde.this if isinstance(desde, exp.From) else None
    if not isinstance(fuente, exp.Table):
        raise SubconsultaNoSoportada("IN requiere una sola fuente de tabla")
    nombre_fuente = fuente.name.lower()
    filas_fuente = tablas.get(nombre_fuente)
    if not filas_fuente:
        raise SubconsultaNoSoportada(
            f"la fuente '{nombre_fuente}' no está disponible con un esquema verificable"
        )

    alias = fuente.alias.lower() if fuente.alias else nombre_fuente
    calificadores = {alias, nombre_fuente}
    columnas = list(select.find_all(exp.Column))
    for referencia in columnas:
        calificador = referencia.table.lower()
        if calificador and calificador not in calificadores:
            raise SubconsultaNoSoportada(
                f"referencia correlacionada o alias externo no soportado: {referencia.sql()}"
            )
        nombre = referencia.name.lower()
        if any(not any(str(clave).lower() == nombre for clave in fila) for fila in filas_fuente):
            raise SubconsultaNoSoportada(
                f"columna '{nombre}' no verificable en la fuente '{nombre_fuente}'"
            )

    where = select.args.get("where")
    filas = (
        filtrar(filas_fuente, where.this.sql(), tablas)
        if isinstance(where, exp.Where)
        else filas_fuente
    )
    valores = [columna(fila, proyectada.name) for fila in filas]
    return valores


def _literal(valor: object) -> exp.Expression:
    if semantica.es_faltante(valor):
        return exp.Null()
    if isinstance(valor, str):
        return exp.Literal.string(valor)
    if isinstance(valor, (int, float, Decimal)) and not isinstance(valor, bool):
        return exp.Literal.number(str(valor))
    raise SubconsultaNoSoportada(f"tipo de valor no soportado en IN: {type(valor).__name__}")


def _expresiones_filtro(operador: Operator) -> list[str]:
    if operador.kind == "filter":
        return [str(operador.params.get("expression") or "")]
    if operador.kind != "map":
        return []
    expresiones = [
        str((paso.get("params") or {}).get("expression") or "")
        for paso in operador.params.get("steps") or []
        if paso.get("kind") == "filter"
    ]
    expresiones.extend(
        str(rama.get("expression") or "") for rama in operador.params.get("branches") or []
    )
    return expresiones


def _subconsultas_de_join(operador: Operator) -> list[dict]:
    """Metadatos de los IN simples que el lowering convirtió en cruces de existencia."""
    if operador.kind == "join":
        pasos = [operador.params]
    elif operador.kind == "map":
        pasos = [
            paso.get("params") or {}
            for paso in operador.params.get("steps") or []
            if paso.get("kind") == "join"
        ]
    else:
        pasos = []
    return [
        metadatos
        for paso in pasos
        if isinstance((metadatos := paso.get("interpreter_subquery")), dict)
    ]


def _fuentes(expresion: exp.Expression) -> set[str]:
    return {
        tabla.name.lower()
        for subconsulta in expresion.find_all(exp.Subquery)
        for tabla in subconsulta.find_all(exp.Table)
    }


def _intervalo_fuente(operador: Operator) -> tuple[int, int] | None:
    """Rango de líneas SAS que identifica cuándo se crea o consume una tabla."""
    if not operador.evidence or len({evidencia.file for evidencia in operador.evidence}) != 1:
        return None
    inicio = min(evidencia.line_start for evidencia in operador.evidence)
    fin = max(evidencia.line_end for evidencia in operador.evidence)
    return (inicio, fin) if inicio > 0 and fin >= inicio else None


def _agregar_dependencias_versionadas(
    plan: Plan,
    dependencias: dict[str, set[str]],
    tabla: str,
    lector: str,
    productores: set[str],
    operadores: dict[str, Operator],
) -> None:
    """Ordena lecturas de subconsulta respecto de las escrituras SAS previas y futuras."""
    intervalo_lector = _intervalo_fuente(operadores[lector])
    intervalos = {productor: _intervalo_fuente(operadores[productor]) for productor in productores}
    if intervalo_lector is None or any(intervalo is None for intervalo in intervalos.values()):
        raise SubconsultaNoSoportada(
            f"el orden de lectura y escritura de '{tabla}' no tiene evidencia de línea suficiente"
        )

    inicio_lector, fin_lector = intervalo_lector
    anteriores = []
    posteriores = []
    ambiguos = []
    for productor, intervalo in intervalos.items():
        inicio, fin = intervalo
        if fin < inicio_lector:
            anteriores.append((fin, inicio, productor))
        elif inicio > fin_lector:
            posteriores.append((inicio, fin, productor))
        elif plan.graph.reaches(productor, lector):
            anteriores.append((fin, inicio, productor))
        elif plan.graph.reaches(lector, productor):
            posteriores.append((inicio, fin, productor))
        else:
            ambiguos.append(productor)

    if ambiguos:
        raise SubconsultaNoSoportada(
            f"la versión de '{tabla}' no se puede determinar por su evidencia de origen"
        )

    anteriores.sort()
    posteriores.sort()
    for (_, _, anterior), (_, _, siguiente) in zip(anteriores, anteriores[1:], strict=False):
        dependencias[siguiente].add(anterior)
    for (_, _, anterior), (_, _, siguiente) in zip(posteriores, posteriores[1:], strict=False):
        dependencias[siguiente].add(anterior)

    if anteriores:
        dependencias[lector].add(anteriores[-1][2])
    if posteriores:
        dependencias[posteriores[0][2]].add(lector)


def orden_de_ejecucion(
    plan: Plan, *, nombres: Nombres, parsear: Parsear
) -> list[str]:
    """Respeta las dependencias de tablas derivadas que el grafo no expresa dentro del SQL."""
    original = list(plan.graph.topological())
    rango = {operador_id: indice for indice, operador_id in enumerate(original)}
    operadores = {operador_id: plan.graph.operator(operador_id) for operador_id in original}
    productores: dict[str, set[str]] = {}
    tipos_productores = {
        "map",
        "filter",
        "derive",
        "select",
        "rename",
        "join",
        "sort",
        "dedup",
        "aggregate",
        "union",
        "stateful_row",
    }
    for operador_id, operador in operadores.items():
        if operador.kind not in tipos_productores:
            continue
        for nombre in nombres(operador):
            productores.setdefault(nombre.lower(), set()).add(operador_id)

    dependencias = {
        operador_id: set(plan.graph.predecessors(operador_id)) for operador_id in original
    }
    for operador_id, operador in operadores.items():
        for texto in _expresiones_filtro(operador):
            if not texto.strip():
                continue
            arbol = parsear(texto)
            for fuente in _fuentes(arbol):
                candidatos = productores.get(fuente, set())
                if operador_id in candidatos:
                    raise SubconsultaNoSoportada(
                        f"dependencia cíclica de subconsulta para la fuente '{fuente}'"
                    )
                if candidatos:
                    _agregar_dependencias_versionadas(
                        plan, dependencias, fuente, operador_id, candidatos, operadores
                    )
        for metadatos in _subconsultas_de_join(operador):
            # La lectura alimenta una cadena intermedia, pero esta operación es la que consume
            # finalmente la versión. Las escrituras futuras deben quedar detrás del cruce completo.
            lector = operador_id
            arbol = parsear(str(metadatos.get("expression") or ""))
            for fuente in _fuentes(arbol):
                candidatos = productores.get(fuente, set())
                if lector in candidatos:
                    raise SubconsultaNoSoportada(
                        f"dependencia cíclica de subconsulta para la fuente '{fuente}'"
                    )
                if candidatos:
                    _agregar_dependencias_versionadas(
                        plan, dependencias, fuente, lector, candidatos, operadores
                    )

    siguientes: dict[str, list[str]] = {operador_id: [] for operador_id in original}
    pendientes = {}
    listos = []
    for operador_id, anteriores in dependencias.items():
        pendientes[operador_id] = len(anteriores)
        if not anteriores:
            heappush(listos, (rango[operador_id], operador_id))
        for anterior in anteriores:
            siguientes[anterior].append(operador_id)

    orden = []
    while listos:
        _, operador_id = heappop(listos)
        orden.append(operador_id)
        for siguiente in siguientes[operador_id]:
            pendientes[siguiente] -= 1
            if pendientes[siguiente] == 0:
                heappush(listos, (rango[siguiente], siguiente))
    if len(orden) != len(original):
        raise SubconsultaNoSoportada("dependencia cíclica entre operadores de subconsulta")
    return orden


def preparar(
    arbol: exp.Expression,
    filas: list[dict],
    tablas: dict[str, list[dict]] | None,
    *,
    filtrar: Filtrar,
    evaluar: Evaluar,
    columna: Columna,
) -> exp.Expression:
    """Reemplaza cada IN con SELECT independiente por su lista de literales validada."""
    nodos = list(_lista_inicial(arbol))
    if nodos and tablas is None:
        raise SubconsultaNoSoportada("IN con SELECT requiere el contexto de tablas")
    preparado = arbol.copy()
    reemplazos = list(_lista_inicial(preparado))

    for nodo in reemplazos:
        valores = _valores(
            nodo.args["query"],
            tablas or {},
            filtrar=filtrar,
            evaluar=evaluar,
            columna=columna,
        )
        if any(semantica.es_faltante(evaluar(nodo.this, fila)) for fila in filas):
            raise SubconsultaNoSoportada("el operando externo de IN contiene un valor faltante")
        presentes = [valor for valor in valores if not semantica.es_faltante(valor)]
        if valores and not presentes:
            raise SubconsultaNoSoportada("la columna de la subconsulta contiene un valor faltante")
        nodo.set("expressions", [_literal(valor) for valor in valores])
        nodo.set("query", None)

    return preparado
