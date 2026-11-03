"""Vista por sección: una caja por sección del programa, o por tramo de una sección muy grande.

Una sección con más de `SECCION_MAX_PASOS` pasos se parte en tramos consecutivos según el
dataset que escribe cada paso. Un paso sin escritura (por ejemplo, una macro dinámica) sigue al
tramo anterior. Así una sección de cientos de pasos deja de ser una sola caja sin detalle.
"""

from __future__ import annotations

from sgm.flow.model import (
    SECCION_SIN_NOMBRE,
    FlowEdge,
    FlowModel,
    FlowStep,
    assign_layers,
)

SECCION_MAX_PASOS = 150
SIN_ESCRITURA = "(inicio)"


def _tramos(nombre: str, pasos: list[FlowStep]) -> list[tuple[str, list[FlowStep]]]:
    """La sección tal cual, o sus tramos si es muy grande."""
    if len(pasos) <= SECCION_MAX_PASOS:
        return [(nombre, pasos)]
    tramos: list[tuple[str, list[FlowStep]]] = []
    clave_actual: str | None = None
    clave = SIN_ESCRITURA
    for paso in pasos:
        if paso.writes:
            clave = paso.writes[0]
        if clave != clave_actual:
            tramos.append((f"{nombre} · {clave}", []))
            clave_actual = clave
        tramos[-1][1].append(paso)
    return tramos


def _agrupar(model: FlowModel) -> tuple[dict[str, list[FlowStep]], dict[str, str], set[str]]:
    """Grupos en orden de aparición, el grupo de cada paso por id, y cuáles son tramos."""
    por_seccion: dict[str, list[FlowStep]] = {}
    for paso in model.steps:
        por_seccion.setdefault(paso.label or SECCION_SIN_NOMBRE, []).append(paso)
    grupos: dict[str, list[FlowStep]] = {}
    grupo_de: dict[str, str] = {}
    tramos: set[str] = set()
    for nombre, pasos in por_seccion.items():
        for tramo, items in _tramos(nombre, pasos):
            grupos[tramo] = items
            if tramo != nombre:
                tramos.add(tramo)
            for paso in items:
                grupo_de[paso.id] = tramo
    return grupos, grupo_de, tramos


def by_section(model: FlowModel) -> FlowModel:
    """Modelo con un nodo por grupo (sección o tramo), y las conexiones entre grupos.

    Las entradas externas siguen igual. Cada conexión entre grupos lleva el dataset que la une; las
    conexiones repetidas o internas al grupo se quitan.
    """
    grupos, grupo_de, tramos = _agrupar(model)
    ids = {nombre: f"s{numero}" for numero, nombre in enumerate(grupos, 1)}
    nodos = []
    for nombre, pasos in grupos.items():
        tipo = "Tramo" if nombre in tramos else "Sección"
        nodos.append(
            FlowStep(
                id=ids[nombre],
                file=pasos[0].file,
                line=pasos[0].line,
                label=nombre,
                kind="section",
                type_name=f"{tipo} · {len(pasos)} pasos",
                title=nombre,
            )
        )

    def nodo_de(paso_id: str) -> str:
        return ids[grupo_de[paso_id]] if paso_id in grupo_de else paso_id

    aristas: list[FlowEdge] = []
    vistas: set[tuple[str, str, str]] = set()
    for arista in model.edges:
        origen, destino = nodo_de(arista.source), nodo_de(arista.target)
        if origen == destino or (origen, destino, arista.dataset) in vistas:
            continue
        vistas.add((origen, destino, arista.dataset))
        aristas.append(FlowEdge(origen, destino, arista.dataset))
    assign_layers(nodos, aristas)
    return FlowModel(
        model.program,
        nodos,
        model.inputs,
        aristas,
        model.external_inputs,
        model.config,
        model.pending,
    )
