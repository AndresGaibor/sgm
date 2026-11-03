"""Diseño del grafo del flujo en SVG: una columna por capa, una caja por paso y una curva
por dataset.

Las entradas externas van en la columna 0. Cada paso va en la columna de su capa, de izquierda a
derecha, y las curvas nunca van hacia atrás porque cada capa es mayor que la de sus predecesores.
"""

from __future__ import annotations

from html import escape

from sgm.flow.model import FlowModel, FlowStep

CAJA_W = 236
CAJA_H = 78
GAP_X = 120
GAP_Y = 26
MARGEN = 28
_CLASE_POR_TIPO = {
    "data": "k-data",
    "sql": "k-sql",
    "proc": "k-proc",
    "external": "k-external",
    "dynamic": "k-dynamic",
    "unparsed": "k-unparsed",
    "section": "k-section",
}


def _corta(text: str, largo: int) -> str:
    return text if len(text) <= largo else text[: largo - 1] + "…"


def _columns(model: FlowModel) -> dict[int, list[FlowStep]]:
    """Nodos por columna, en el orden de línea dentro de cada una."""
    columns: dict[int, list[FlowStep]] = {}
    for node in model.inputs:
        columns.setdefault(0, []).append(node)
    for step in model.steps:
        columns.setdefault(step.layer, []).append(step)
    return columns


def positions(model: FlowModel) -> dict[str, tuple[int, int]]:
    """Esquina superior izquierda de cada nodo, por id."""
    out: dict[str, tuple[int, int]] = {}
    for layer, nodes in _columns(model).items():
        for row, node in enumerate(nodes):
            x = MARGEN + layer * (CAJA_W + GAP_X)
            y = MARGEN + row * (CAJA_H + GAP_Y)
            out[node.id] = (x, y)
    return out


def _size(model: FlowModel) -> tuple[int, int]:
    columns = _columns(model)
    if not columns:
        return 2 * MARGEN, 2 * MARGEN
    cols = max(columns) + 1
    rows = max(len(nodes) for nodes in columns.values())
    width = 2 * MARGEN + cols * CAJA_W + (cols - 1) * GAP_X
    height = 2 * MARGEN + rows * CAJA_H + (rows - 1) * GAP_Y
    return width, height


def _node_svg(node: FlowStep, x: int, y: int) -> str:
    clase = _CLASE_POR_TIPO.get(node.kind, "k-proc")
    reads = ", ".join(node.reads) or "nada"
    writes = ", ".join(node.writes) or "nada"
    tooltip = f"{node.type_name}: {node.title}\nlee: {reads}\nescribe: {writes}"
    if node.file:
        tooltip += f"\n{node.file}:{node.line}"
    where = f"{node.file}:{node.line}" if node.kind != "external" else "dataset del programa"
    if node.kind == "external":
        href = f"#entrada-{node.id}"
    elif node.kind == "section":
        href = "#pasos"
    else:
        href = f"#paso-{node.id}"
    return (
        f'<a href="{href}"><g class="nodo {clase}">'
        f"<title>{escape(tooltip)}</title>"
        f'<rect x="{x}" y="{y}" width="{CAJA_W}" height="{CAJA_H}" rx="10"/>'
        f'<text class="tipo" x="{x + 14}" y="{y + 22}">{escape(node.type_name)}</text>'
        f'<text class="titulo" x="{x + 14}" y="{y + 44}">{escape(_corta(node.title, 30))}</text>'
        f'<text class="sub" x="{x + 14}" y="{y + 63}">{escape(_corta(where, 34))}</text>'
        "</g></a>"
    )


def _edge_svg(
    model: FlowModel,
    pos: dict[str, tuple[int, int]],
    index: int,
    source: str,
    target: str,
    dataset: str,
) -> str:
    x1, y1 = pos[source][0] + CAJA_W, pos[source][1] + CAJA_H // 2
    x2, y2 = pos[target][0], pos[target][1] + CAJA_H // 2
    half = GAP_X // 2
    path = f"M{x1},{y1} C{x1 + half},{y1} {x2 - half},{y2} {x2},{y2}"
    mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
    return (
        f'<g class="arista"><path d="{path}" marker-end="url(#flecha)"/>'
        f'<text x="{mid_x}" y="{mid_y - 6 - (index % 3) * 13}">{escape(_corta(dataset, 26))}</text>'
        "</g>"
    )


def render_svg(model: FlowModel) -> str:
    """SVG completo del flujo. Sin nodos, devuelve un lienzo vacío con un mensaje."""
    width, height = _size(model)
    if not model.steps:
        return (
            f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            'role="img" aria-label="Sin pasos"><text x="28" y="40">'
            "El programa no tiene pasos de datos.</text></svg>"
        )
    pos = positions(model)
    nodes = {node.id: node for node in [*model.inputs, *model.steps]}
    edges = "".join(
        _edge_svg(model, pos, i, e.source, e.target, e.dataset) for i, e in enumerate(model.edges)
    )
    boxes = "".join(_node_svg(node, *pos[node.id]) for node in nodes.values())
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" '
        f'aria-label="Flujo de datos del programa {escape(model.program)}">'
        '<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker>'
        "</defs>"
        f"{edges}{boxes}</svg>"
    )
