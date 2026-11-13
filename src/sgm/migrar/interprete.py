"""Intérprete del plan: ejecuta los operadores sobre filas y devuelve las tablas de `WORK`.

Es el anillo B de la verificación: prueba que el plan —y por lo tanto el Job que sale de él— calcula
lo que el SAS dice, sin abrir Talend Studio. Sirve para dos cosas que ninguna otra pieza cubre: los
casos donde Studio no está disponible, y el contraste con `esperado/` de todo el corpus.

Soporta lo que la primera rebanada vertical traduce: `read_file`, `write_file`, `map` con pasos
`join` (inner y left), `filter` y `derive`, más los `read` y `write` que solo nombran un
conjunto. Lo demás **no se ignora**: lanza `NoSoportadoEnInterprete` con el operador o el paso
que no entiende. Un intérprete que se salta un `sort` en silencio daría filas correctas en el
conjunto y falsas en el orden, y la prueba pasaría sin probar nada.

Las expresiones se leen con `sqlglot`, que ya es dependencia del proyecto para el SQL, y se evalúan
con la semántica de `sgm.migrar.semantica`. Las columnas se resuelven por nombre y sin distinguir
mayúsculas: el calificador (`ventas.monto`) se ignora, así que en un auto-unión las dos tablas
comparten nombre de columna y la última en entrar gana. Es una limitación conocida, anotada en
`PROGRESS.md`, no un descuido: el plan tampoco distingue los alias de una auto-unión.
"""

from __future__ import annotations

import copy
import re

from sgm.ir.desplegar import plan_desplegado
from sgm.ir.models import Operator, Plan
from sgm.migrar import semantica
from sgm.migrar.interprete_agregados import AgregadoNoSoportado, agregar
from sgm.migrar.interprete_subconsultas import (
    SubconsultaNoSoportada,
    _fuentes,
    orden_de_ejecucion,
    preparar,
)

# Operadores que el intérprete sabe ejecutar; el resto detiene la ejecución con su nombre.
SOPORTADOS = frozenset(
    {"read", "read_file", "write", "write_file", "map", "join", "filter", "derive"}
)
# Pasos que el plan también deja sueltos, sin el `map` que los envuelve.
_PASOS_SUELTOS = (
    "filter", "derive", "select", "rename", "sort", "dedup", "aggregate", "stateful_row"
)
_TIPOS_DE_UNION = frozenset({"inner", "left", "left outer", "cross"})


from sgm.migrar.interprete_valores import (  # noqa: E402 - movido, ver interprete_valores.py
    NoSoportadoEnInterprete,
    _arbol,
    _columna,
    _numero,
    _primero,
    _tabla,
    _valor,
    _verdad,
)


def _clave(valor: object) -> tuple:
    """Llave de unión con la comparación de SAS: el faltante es un valor, el texto sin blancos."""
    if semantica.es_faltante(valor):
        return (0, 0.0, "")
    numero = _numero(valor)
    if numero is not None:
        return (1, numero, "")
    return (2, 0.0, semantica.como_texto(valor))


def _filtrar(
    filas: list[dict], expresion: str, tablas: dict[str, list[dict]] | None = None
) -> list[dict]:
    arbol = _arbol(expresion)
    try:
        arbol = preparar(
            arbol,
            filas,
            tablas,
            filtrar=_filtrar,
            evaluar=_valor,
            columna=_columna,
        )
    except SubconsultaNoSoportada as error:
        raise NoSoportadoEnInterprete("subconsulta", str(error)) from error
    return [fila for fila in filas if _verdad(_valor(arbol, fila))]


def _validar_subconsulta_de_union(
    params: dict, actual: list[dict], plan: Plan, por_operador: dict, tablas: dict
) -> None:
    """Valida el IN original antes de ejecutar el cruce que lo representa en el plan."""
    metadatos = params.get("interpreter_subquery")
    if not isinstance(metadatos, dict):
        return
    lector = str(metadatos.get("source_read") or "")
    contexto = dict(tablas)
    if lector in por_operador:
        fuente = plan.graph.operator(lector)
        nombre = _tabla(fuente.params.get("dataset", ""))
        if nombre:
            contexto[nombre] = por_operador[lector]
    fuentes = _fuentes(_arbol(str(metadatos.get("expression") or "")))
    if any(nombre not in contexto for nombre in fuentes):
        # El plan optimizado ya materializa las llaves del IN. No volver a evaluar la subconsulta
        # si su fuente intermedia fue plegada; la validación estructural corresponde al lowering.
        return
    try:
        preparar(
            _arbol(str(metadatos.get("expression") or "")),
            actual,
            contexto,
            filtrar=_filtrar,
            evaluar=_valor,
            columna=_columna,
        )
    except SubconsultaNoSoportada as error:
        raise NoSoportadoEnInterprete("subconsulta", str(error)) from error


def _fila_de(
    pares: list[tuple[str, object, object | None]], fila: dict, secuencial: bool = False
) -> dict:
    """Las columnas de la salida, en el orden de las asignaciones."""
    resultado = {}
    for destino, arbol, condicional in pares:
        contexto = {**fila, **resultado} if secuencial else fila
        if condicional is None:
            valor = _valor(arbol, contexto)
        elif isinstance(condicional, dict):
            valor = None
            for condicion, rama in condicional["branches"]:
                if _verdad(_valor(condicion, contexto)):
                    valor = _valor(rama, contexto)
                    break
            else:
                valor = _valor(condicional["otherwise"], contexto)
        else:
            condicion, alternativa = condicional
            rama = arbol if _verdad(_valor(condicion, contexto)) else alternativa
            valor = _valor(rama, contexto)
        resultado[destino] = semantica.a_texto(valor)
    return resultado


def _proyectar(filas: list[dict], asignaciones: list[dict], aditivo: bool) -> list[dict]:
    """Cada asignación es una columna de la salida.

    Un `SELECT` reemplaza la fila —solo salen sus columnas— y una asignación de DATA step le agrega
    columnas a la que ya había. El plan lo dice con `modo: agrega`, que pone el traductor del DATA
    step; sin la marca, el `derive` es una proyección.
    """
    if not asignaciones:
        return filas
    pares = []
    for asignacion in asignaciones:
        condicion = asignacion.get("conditional")
        condicional = None
        if isinstance(condicion, dict):
            if condicion.get("branches"):
                condicional = {
                    "branches": [
                        (
                            _arbol(str(rama.get("condition") or "")),
                            _arbol(str(rama.get("expression") or "")),
                        )
                        for rama in condicion["branches"]
                    ],
                    "otherwise": _arbol(str(condicion.get("otherwise") or "")),
                }
            else:
                condicional = (
                    _arbol(str(condicion.get("condition") or "")),
                    _arbol(str(condicion.get("otherwise") or "")),
                )
        pares.append(
            (
                str(asignacion.get("target") or ""),
                _arbol(str(asignacion.get("expression") or "")),
                condicional,
            )
        )
    if aditivo:
        return [{**fila, **_fila_de(pares, fila, secuencial=True)} for fila in filas]
    return [_fila_de(pares, fila) for fila in filas]


def _seleccionar(filas: list[dict], params: dict) -> list[dict]:
    """Aplica KEEP o DROP como proyección de columnas, sin cambiar el orden de la fila."""
    nombres = {str(nombre).lower() for nombre in params.get("names") or []}
    modo = str(params.get("mode") or "").lower()
    if modo == "keep":
        return [
            {nombre: valor for nombre, valor in fila.items() if nombre.lower() in nombres}
            for fila in filas
        ]
    if modo == "drop":
        return [
            {nombre: valor for nombre, valor in fila.items() if nombre.lower() not in nombres}
            for fila in filas
        ]
    raise NoSoportadoEnInterprete("select", f"modo '{modo}'")


def _renombrar(filas: list[dict], params: dict) -> list[dict]:
    """Renombra variables solo en la fila de salida (`lestmtsref`, pp. 326-327)."""
    cambios = {
        str(origen).lower(): str(destino).lower()
        for origen, destino in params.get("pairs") or []
    }
    return [
        {cambios.get(str(nombre).lower(), nombre): valor for nombre, valor in fila.items()}
        for fila in filas
    ]


def _unir(izquierda: list[dict], derecha: list[dict], params: dict) -> list[dict]:
    """Inner y left join por llaves; una llave repetida da una fila por pareja, como en SQL."""
    tipo = str(params.get("join_type") or "inner").strip().lower()
    if tipo not in _TIPOS_DE_UNION:
        raise NoSoportadoEnInterprete("join", f"tipo '{tipo}'")
    pares = [list(par) for par in params.get("keys") or [] if len(list(par)) == 2]
    if tipo == "cross" or not pares:
        if tipo == "cross":
            return [{**fila, **otra} for fila in izquierda for otra in derecha]
        raise NoSoportadoEnInterprete("join", f"'{tipo}' sin llaves demostrables")
    arboles = [(_arbol(str(uno)), _arbol(str(otro))) for uno, otro in pares]
    indice: dict[tuple, list[dict]] = {}
    for fila in derecha:
        llave = tuple(_clave(_valor(arbol, fila)) for _, arbol in arboles)
        indice.setdefault(llave, []).append(fila)
    vacia = dict.fromkeys(derecha[0], None) if derecha else {}
    resultado: list[dict] = []
    for fila in izquierda:
        llave = tuple(_clave(_valor(arbol, fila)) for arbol, _ in arboles)
        parejas = indice.get(llave)
        if parejas:
            resultado += [{**fila, **otra} for otra in parejas]
        elif tipo in ("left", "left outer"):
            resultado.append({**vacia, **fila})
    return resultado


def _mezclar(entradas: list[list[dict]], banderas: list[str | None], params: dict) -> list[dict]:
    """`MERGE ... BY k` de un DATA step: junta por grupo de llave, fila con fila, no por producto.

    Dentro de un grupo la fila `j` de cada tabla va con la fila `j` de las demás. A la tabla que se
    queda sin filas se le mantienen los últimos valores; a la que no tiene el grupo, ninguno. Las
    columnas con el mismo nombre las pisa la última tabla que aporta fila. `IN=` vale 1 solo si la
    tabla aportó una fila a esa salida. Salida ordenada por la llave, como exige el `BY`.
    """
    llaves = [str(n).split(".")[-1].lower() for n in params.get("by") or []]
    grupos: list[dict[tuple, list[dict]]] = []
    for filas in entradas:
        por_llave: dict[tuple, list[dict]] = {}
        for fila in filas:
            por_llave.setdefault(tuple(_clave(_columna(fila, k)) for k in llaves), []).append(fila)
        grupos.append(por_llave)
    columnas: list[str] = []
    for filas in entradas:
        for fila in filas[:1]:
            columnas += [c for c in fila if c not in columnas]
    tipo = str(params.get("join_type") or "full").strip().lower()
    resultado: list[dict] = []
    for llave in sorted({k for g in grupos for k in g}):
        miembros = [g.get(llave, []) for g in grupos]
        for posicion in range(max(len(m) for m in miembros)):
            fila = dict.fromkeys(columnas)
            presentes = []
            for filas in miembros:
                if filas:
                    fila.update(filas[min(posicion, len(filas) - 1)])
                # La bandera `IN=` sigue en 1 mientras la tabla tiene valores retenidos en el grupo.
                presentes.append(bool(filas))
            if tipo == "inner" and not all(presentes):
                continue
            if tipo == "left" and not presentes[0]:
                continue
            if tipo == "right" and not presentes[1]:
                continue
            for nombre, aporto in zip(banderas, presentes, strict=True):
                if nombre:
                    fila[nombre.lower()] = 1 if aporto else 0
            resultado.append(fila)
    return resultado


def _derecha(params: dict) -> str | None:
    """Tabla del lado derecho de la unión: la que califica el segundo elemento de la primera llave.

    Es lo único que dice qué entrada del mapa es la de la derecha: el orden de los predecesores
    en el grafo no lo dice, porque el plegado de `read` mete aristas de más.
    """
    for par in params.get("keys") or []:
        partes = str(list(par)[1]).split(".") if len(list(par)) == 2 else []
        if len(partes) == 2:
            return _tabla(partes[0])
    return None


def _nombre_de_columna(filas: list[dict], nombre: object) -> str:
    """Columna que nombra un `ORDER BY` o `DISTINCT`: por nombre o por posición (`ORDER BY 2`)."""
    texto = str(nombre).strip()
    if texto.isdigit() and filas:
        columnas = list(filas[0])
        posicion = int(texto)
        if 1 <= posicion <= len(columnas):
            return columnas[posicion - 1]
    return texto


def _llaves(filas: list[dict], params: dict) -> list[str]:
    """Columnas del `BY`; `_ALL_` son todas las de la fila."""
    nombres: list[str] = []
    for nombre in params.get("by") or []:
        if str(nombre).strip().lower() == "_all_":
            nombres += list(filas[0]) if filas else []
        else:
            nombres.append(_nombre_de_columna(filas, nombre))
    return nombres


def _ordenar(filas: list[dict], params: dict) -> list[dict]:
    """`ORDER BY` de PROC SQL: el faltante va primero en ascendente (`sqlproc`); orden estable.

    Se ordena de la última llave a la primera, cada una con su sentido; como el orden de Python es
    estable, las filas que empatan en todas las llaves conservan el orden en que llegaron.
    """
    llaves = _llaves(filas, params)
    sentidos = list(params.get("descending") or [])
    resultado = list(filas)
    for posicion in range(len(llaves) - 1, -1, -1):
        descendente = posicion < len(sentidos) and bool(sentidos[posicion])
        llave = llaves[posicion]
        resultado.sort(
            key=lambda fila, llave=llave: _clave(_columna(fila, llave)), reverse=descendente
        )
    return resultado


def _unicos(filas: list[dict], params: dict) -> list[dict]:
    """`SELECT DISTINCT`: la primera fila de cada combinación de llaves; faltante = faltante."""
    llaves = _llaves(filas, params)
    vistas: set[tuple] = set()
    resultado: list[dict] = []
    for fila in filas:
        clave = tuple(_clave(_columna(fila, llave)) for llave in llaves)
        if clave not in vistas:
            vistas.add(clave)
            resultado.append(fila)
    return resultado


_AGREGADO = re.compile(
    r"^\s*(count|sum|avg|mean|min|max)\s*\(\s*(distinct\s+)?(\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)\s*$",
    re.IGNORECASE,
)


def _calcular(funcion: str, distinto: bool, nombre: str, filas: list[dict]) -> object:
    """Un agregado de `PROC SQL` sobre un grupo: ignora los faltantes; sin valores, es faltante.

    `COUNT(*)` cuenta filas; `COUNT(col)` las no faltantes; `SUM`, `AVG`, `MIN` y `MAX` solo miran
    valores presentes (`sqlproc`, funciones de resumen).
    """
    if nombre == "*":
        return len(filas)
    presentes = [
        valor
        for valor in (_columna(fila, nombre.split(".")[-1]) for fila in filas)
        if not semantica.es_faltante(valor)
    ]
    if funcion == "count":
        return len({_clave(v) for v in presentes}) if distinto else len(presentes)
    if not presentes:
        return None
    if funcion in ("min", "max"):
        elegir = min if funcion == "min" else max
        return elegir(presentes, key=_clave)
    numeros = [n for n in (_numero(v) for v in presentes) if n is not None]
    if not numeros:
        return None
    return sum(numeros) if funcion == "sum" else sum(numeros) / len(numeros)


def _limites(filas: list[dict], llaves: list[str]) -> list[dict]:
    """Por fila, `first.v` y `last.v` de cada variable del `BY` (1 o 0), como el SAS.

    Con varias variables, `first.v` es 1 si cambió `v` o cualquiera de las anteriores.
    """
    claves = [tuple(_clave(_columna(fila, k)) for k in llaves) for fila in filas]
    resultado = []
    for i in range(len(filas)):
        marcas: dict[str, int] = {}
        for k, nombre in enumerate(llaves):
            antes = claves[i - 1][: k + 1] if i else None
            despues = claves[i + 1][: k + 1] if i + 1 < len(filas) else None
            marcas[f"first.{nombre}"] = 1 if antes != claves[i][: k + 1] else 0
            marcas[f"last.{nombre}"] = 1 if despues != claves[i][: k + 1] else 0
        resultado.append(marcas)
    return resultado


def _por_grupo(filas: list[dict], params: dict) -> list[dict]:
    """Programa por fila de un DATA step con `BY`: retención, suma, `FIRST.`/`LAST.` y `IF`.

    Las variables retenidas (las del `RETAIN` y las de una sentencia de suma, que empiezan en 0)
    conservan su valor de una fila a la siguiente; las demás variables nuevas empiezan cada fila en
    faltante. Una fila que no pasa un `IF cond;` no sale, pero lo que dejó en las retenidas queda.
    """
    llaves = [str(n).lower() for n in params.get("by") or []]
    programa = params.get("programa") or []
    retenidas: dict[str, object] = {}
    for paso in programa:
        if paso["op"] == "retain":
            inicial = paso.get("valor")
            valor = None if inicial is None else _valor(_arbol(str(inicial)), {})
            retenidas.update(dict.fromkeys(paso["names"], valor))
        elif paso["op"] == "suma":
            retenidas.setdefault(paso["target"], 0)
    nuevas: list[str] = []
    resultado: list[dict] = []
    for fila, marcas in zip(filas, _limites(filas, llaves), strict=True):
        pdv = {**retenidas, **fila}
        seguir = True
        for paso in programa:
            clase = paso["op"]
            vista = {**pdv, **marcas}
            if clase == "asigna":
                pdv[paso["target"]] = _valor(_arbol(paso["expr"]), vista)
                destino = paso["target"]
            elif clase == "si":
                destino = paso["target"]
                if _verdad(_valor(_arbol(paso["cond"]), vista)):
                    pdv[destino] = _valor(_arbol(paso["expr"]), vista)
            elif clase == "suma":
                destino = paso["target"]
                suma = _numero(_valor(_arbol(paso["expr"]), vista))
                pdv[destino] = (_numero(pdv.get(destino)) or 0) + (suma or 0)
            elif clase == "filtra":
                destino = None
                if not _verdad(_valor(_arbol(paso["cond"]), vista)):
                    seguir = False
            else:
                destino = None
            if destino and destino not in fila and destino not in nuevas:
                nuevas.append(destino)
        for nombre in retenidas:
            if nombre in pdv:
                retenidas[nombre] = pdv[nombre]
            if nombre not in fila and nombre not in nuevas:
                nuevas.append(nombre)
        if seguir:
            resultado.append(pdv)
    columnas = [*(filas[0] if filas else {}), *nuevas]
    return [{c: fila.get(c) for c in columnas} for fila in resultado]


def _agregar(filas: list[dict], params: dict) -> list[dict]:
    """Adapta los agregados compatibles al error público del intérprete."""
    try:
        return agregar(
            filas,
            params,
            parsear=_arbol,
            evaluar=_valor,
            columna=_columna,
            clave=_clave,
        )
    except AgregadoNoSoportado as error:
        raise NoSoportadoEnInterprete("aggregate", str(error)) from error


def _apilar(op: Operator, plan: Plan, tablas: dict, por_operador: dict) -> list[dict]:
    """`SET a b` o `UNION ALL`: las filas de cada entrada una tras otra, juntas por nombre.

    Una columna que una entrada no tiene queda faltante en sus filas, como en SAS. Sin `ALL`
    (`UNION` de PROC SQL) se quitan además las filas repetidas.
    """
    fuentes = [_tabla(nombre) for nombre in op.params.get("sources") or []]
    if fuentes:
        entradas = [tablas.get(nombre, []) for nombre in fuentes]
    else:
        entradas = [por_operador.get(previo, []) for previo in plan.graph.predecessors(op.id)]
    columnas: list[str] = []
    for filas in entradas:
        for fila in filas:
            columnas += [c for c in fila if c not in columnas]
    apiladas = [{c: fila.get(c) for c in columnas} for filas in entradas for fila in filas]
    if op.params.get("all", True):
        return apiladas
    vistas: set[tuple] = set()
    unicas = []
    for fila in apiladas:
        clave = tuple(_clave(valor) for valor in fila.values())
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(fila)
    return unicas


def _entradas(
    plan: Plan, op: Operator, por_operador: dict, tablas: dict | None = None
) -> dict[str, list[dict]]:
    """Filas de cada predecesor, por la tabla que entrega."""
    por_tabla: dict[str, list[dict]] = {}
    for previo in plan.graph.predecessors(op.id):
        for nombre in _nombres(plan.graph.operator(previo)):
            por_tabla.setdefault(
                nombre, (tablas or {}).get(nombre, por_operador.get(previo, []))
            )
    return por_tabla


def _base(
    plan: Plan,
    op: Operator,
    derechos: set[str],
    por_operador: dict,
    tablas: dict | None = None,
) -> list[dict]:
    """La entrada que se acumula: el primer predecesor que no es el lado derecho de una unión."""
    previos = plan.graph.predecessors(op.id)
    for previo in previos:
        operador_previo = plan.graph.operator(previo)
        if operador_previo.kind == "map" and any(
            rama.get("continue") for rama in operador_previo.params.get("branches") or []
        ):
            return por_operador.get(previo, [])
        nombres = _nombres(operador_previo)
        if not nombres or not set(nombres) <= derechos:
            nombre = next((nombre for nombre in nombres if nombre in (tablas or {})), None)
            return (tablas or {}).get(nombre, por_operador.get(previo, []))
    return por_operador.get(previos[0], []) if previos else []


def _pasos(op: Operator, plan: Plan, por_operador: dict, tablas: dict | None = None) -> list[dict]:
    """Los pasos de un `map` —o el operador suelto— sobre las entradas, en el orden del plan."""
    pasos = op.params.get("steps")
    if not pasos and op.kind != "map":
        pasos = [{"kind": op.kind, "params": op.params}]
    pasos = pasos or []
    por_tabla = _entradas(plan, op, por_operador, tablas)
    derechos = {
        _derecha(paso.get("params") or {}) for paso in pasos if paso.get("kind") == "join"
    }
    actual = _base(plan, op, {d for d in derechos if d}, por_operador, tablas)
    entrada_declarada = _primero(op.params, "inputs")
    if entrada_declarada:
        actual = por_tabla.get(_tabla(entrada_declarada), actual)
    for paso in pasos:
        clase = str(paso.get("kind") or "")
        params = paso.get("params") or {}
        if clase == "join" and not params.get("keys") and params.get("by"):
            fuentes = [_tabla(s) for s in params.get("sources") or []]
            if len(fuentes) < 2 or any(f not in por_tabla for f in fuentes):
                raise NoSoportadoEnInterprete("join", "MERGE sin las tablas de sus fuentes")
            banderas = {
                _tabla(plan.graph.operator(p).params.get("dataset", "")): plan.graph.operator(
                    p
                ).params.get("in")
                for p in plan.graph.predecessors(op.id)
                if plan.graph.operator(p).kind == "read"
            }
            actual = _mezclar(
                [por_tabla[f] for f in fuentes], [banderas.get(f) for f in fuentes], params
            )
        elif clase == "join":
            _validar_subconsulta_de_union(params, actual, plan, por_operador, por_tabla)
            tabla = _derecha(params)
            if tabla not in por_tabla:
                raise NoSoportadoEnInterprete(
                    "join", f"no hay una entrada para la tabla '{tabla}'"
                )
            actual = _unir(actual, por_tabla[tabla], params)
        elif clase == "filter":
            actual = _filtrar(actual, str(params.get("expression") or ""), por_tabla)
        elif clase == "derive":
            asignaciones = _expandir_estrellas(params.get("assignments") or [], por_tabla)
            actual = _proyectar(
                actual, asignaciones, aditivo=params.get("modo") == "agrega"
            )
        elif clase == "select":
            actual = _seleccionar(actual, params)
        elif clase == "rename":
            actual = _renombrar(actual, params)
        elif clase == "sort":
            actual = _ordenar(actual, params)
        elif clase == "dedup":
            actual = _unicos(actual, params)
        elif clase == "aggregate":
            actual = _agregar(actual, params)
        elif clase == "stateful_row" and params.get("reason") == "by_group":
            actual = _por_grupo(actual, params)
        else:
            raise NoSoportadoEnInterprete(clase or "paso", "el intérprete no lo ejecuta")
    return actual


def _nombres(op: Operator) -> list[str]:
    """Conjuntos de `WORK` bajo los que queda el resultado del operador."""
    clases = (*_PASOS_SUELTOS, "read_file", "map", "join", "union", "split")
    if op.kind in clases:
        outputs = op.params.get("outputs") or []
        if op.kind == "split":
            outputs = op.params.get("targets") or (
                [op.params["target"]] if op.params.get("target") else []
            )
        if op.kind == "dedup":
            outputs = [*outputs, *(op.params.get("duplicate_outputs") or [])]
        return [_tabla(nombre) for nombre in outputs]
    if op.kind == "write_file":
        return [_tabla(nombre) for nombre in op.params.get("inputs") or []]
    if op.kind in ("read", "write"):
        return [_tabla(op.params.get("dataset", ""))]
    return []


def _ramas(
    op: Operator, filas: list[dict], tablas: dict[str, list[dict]] | None = None
) -> dict[str, list[dict]]:
    """Un `map` con ramas es un IF/THEN/ELSE que escribe en varias salidas: cada rama su filtro."""
    resultado = {}
    for rama in op.params.get("branches") or []:
        if rama.get("continue"):
            continue
        filas_rama = filas
        join_key = rama.get("joinKey")
        if join_key:
            if rama.get("rejectInnerJoin"):
                filas_rama = [fila for fila in filas if _columna(fila, str(join_key)) is None]
            elif rama.get("matched"):
                filas_rama = [fila for fila in filas if _columna(fila, str(join_key)) is not None]
        if rama.get("expression"):
            filas_rama = _filtrar(filas_rama, str(rama["expression"]), tablas)
        resultado[_tabla(rama.get("outputs", ["WORK.sin_nombre"])[0])] = filas_rama
    return resultado


def _expandir_estrellas(asignaciones: list[dict], por_tabla: dict[str, list[dict]]) -> list[dict]:
    """Expande `alias.*` solo si las filas disponibles demuestran su esquema."""
    resultado = []
    for asignacion in asignaciones:
        expresion = str(asignacion.get("expression") or "").strip()
        if not re.fullmatch(r"[\w.]+\.\*", expresion):
            resultado.append(asignacion)
            continue
        tabla = expresion[:-2].lower().split(".")[-1]
        filas = por_tabla.get(tabla)
        if not filas:
            raise NoSoportadoEnInterprete(
                "select", f"el esquema de la fuente '{tabla}' no está verificable"
            )
        for columna in filas[0]:
            resultado.append(
                {
                    "target": columna,
                    "expression": f"{tabla}.{columna}",
                    "origin": "columna",
                }
            )
    return resultado


def _ejecutar(
    op: Operator, plan: Plan, tablas: dict, por_operador: dict
) -> tuple[list[dict], dict[str, list[dict]]]:
    """Filas del operador y las tablas que deja, por nombre sin biblioteca.

    Las dos cosas van juntas porque un operador intermedio —un `join` que alimenta un `map`— no
    tiene tabla propia: sus filas solo se pueden encontrar por su id, y el `map` de detrás las pide
    así.
    """
    if op.kind == "unsupported" and op.params.get("reason") == "CONFIGURACION":
        return [], {}  # `%LET`, `OPTIONS`: ya sustituidos en el programa, no producen filas
    if op.kind in ("read", "read_file"):
        nombre = (
            _tabla(op.params.get("dataset", ""))
            if op.kind == "read"
            else _tabla(_primero(op.params, "outputs"))
        )
        if nombre in tablas:
            return tablas[nombre], {nombre: tablas[nombre]}
        previos = plan.graph.predecessors(op.id)
        filas = por_operador.get(previos[0], []) if previos else []
        return filas, {nombre: filas}
    if op.kind in ("write", "write_file"):
        previos = plan.graph.predecessors(op.id)
        if not previos:
            raise NoSoportadoEnInterprete(op.kind, "sin operador de origen")
        filas = por_operador.get(previos[0], [])
        return filas, {nombre: tablas.get(nombre, filas) for nombre in _nombres(op)}
    if op.kind == "union":
        filas = _apilar(op, plan, tablas, por_operador)
        return filas, {nombre: filas for nombre in _nombres(op)}
    if op.kind == "dedup" and op.params.get("duplicate_outputs"):
        previos = plan.graph.predecessors(op.id)
        entrada = por_operador.get(previos[0], []) if previos else []
        filas = _unicos(entrada, op.params)
        llaves = _llaves(entrada, op.params)
        vistas: set[tuple] = set()
        duplicadas = []
        for fila in entrada:
            clave = tuple(_clave(_columna(fila, nombre)) for nombre in llaves)
            if clave in vistas:
                duplicadas.append(fila)
            else:
                vistas.add(clave)
        propias = {_tabla(nombre): filas for nombre in op.params.get("outputs") or []}
        propias.update(
            {_tabla(nombre): duplicadas for nombre in op.params.get("duplicate_outputs") or []}
        )
        return filas, propias
    if op.kind in ("map", "join", *_PASOS_SUELTOS):
        previos = plan.graph.predecessors(op.id)
        if op.kind == "map" and op.params.get("branches"):
            ejecutable = op
            rechazo_inner = any(
                rama.get("rejectInnerJoin") for rama in op.params["branches"]
            )
            derivaciones = []
            if any(rama.get("rejectInnerJoin") for rama in op.params["branches"]):
                ejecutable = copy.deepcopy(op)
                derivaciones = [
                    paso
                    for paso in ejecutable.params.get("steps") or []
                    if paso.get("kind") == "derive"
                ]
                ejecutable.params["steps"] = [
                    paso
                    for paso in ejecutable.params.get("steps") or []
                    if paso.get("kind") != "derive"
                ]
                for paso in ejecutable.params.get("steps") or []:
                    if paso.get("kind") == "join":
                        paso["params"]["join_type"] = "left"
            filas = _pasos(ejecutable, plan, por_operador, tablas) if op.params.get("steps") else (
                por_operador.get(previos[0], []) if previos else []
            )
            propias = _ramas(op, filas, tablas)
            if rechazo_inner and derivaciones:
                asignaciones = derivaciones[-1].get("params", {}).get("assignments") or []
                propias = {
                    nombre: _proyectar(rama, asignaciones, aditivo=False)
                    for nombre, rama in propias.items()
                }
            return filas, propias
        filas = _pasos(op, plan, por_operador, tablas)
        return filas, {nombre: filas for nombre in _nombres(op)}
    if op.kind == "split":
        previos = plan.graph.predecessors(op.id)
        filas_entrada = por_operador.get(previos[0], []) if previos else []
        condicion = str(op.params.get("condition") or "").strip()
        if condicion:
            salida = _filtrar(filas_entrada, condicion, tablas)
        elif op.params.get("branch") == "else" and previos:
            anterior = plan.graph.operator(previos[0])
            condicion_anterior = str(anterior.params.get("condition") or "").strip()
            salida = (
                [
                    fila
                    for fila in filas_entrada
                    if not _filtrar([fila], condicion_anterior, tablas)
                ]
                if anterior.kind == "split" and condicion_anterior
                else filas_entrada
            )
        else:
            salida = filas_entrada
        return filas_entrada, {nombre: salida for nombre in _nombres(op)}
    raise NoSoportadoEnInterprete(op.kind, "el intérprete no lo ejecuta")


def ejecutar_plan(
    plan: Plan, entradas: dict[str, list[dict[str, str | None]]]
) -> dict[str, list[dict[str, str | None]]]:
    """Ejecuta el plan y devuelve las tablas de `WORK` que produce, por nombre sin biblioteca.

    `entradas` trae las filas de las tablas que el programa lee, con el nombre de la tabla como
    clave (`WORK.clientes`, `clientes` o `CLIENTES` dan igual). Las columnas de cada fila se buscan
    sin distinguir mayúsculas.
    """
    plan, _ = plan_desplegado(plan)  # una plantilla se ejecuta instancia por instancia
    tablas: dict[str, list[dict]] = {
        _tabla(nombre): [{str(c).lower(): v for c, v in fila.items()} for fila in filas]
        for nombre, filas in entradas.items()
    }
    por_operador: dict[str, list[dict]] = {}
    try:
        orden = orden_de_ejecucion(plan, nombres=_nombres, parsear=_arbol)
    except SubconsultaNoSoportada as error:
        raise NoSoportadoEnInterprete("subconsulta", str(error)) from error
    for op_id in orden:
        op = plan.graph.operator(op_id)
        filas, propias = _ejecutar(op, plan, tablas, por_operador)
        por_operador[op.id] = filas
        tablas.update(propias)
    return tablas


__all__ = ["SOPORTADOS", "NoSoportadoEnInterprete", "ejecutar_plan"]
