"""Orden de ejecución de las subconsultas del anillo B: dependencias entre tablas derivadas."""

from __future__ import annotations

from collections.abc import Callable
from heapq import heappop, heappush

from sqlglot import exp

from sgm.ir.models import Operator, Plan

Evaluar = Callable[[exp.Expression, dict], object]
Filtrar = Callable[[list[dict], str, dict | None], list[dict]]
Columna = Callable[[dict, str], object]
Nombres = Callable[[Operator], list[str]]
Parsear = Callable[[str], exp.Expression]


class SubconsultaNoSoportada(ValueError):
    """Forma de subconsulta para la que el anillo B no tiene equivalencia demostrada."""


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
