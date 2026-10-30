"""Análisis de un proyecto SAS: índice de macros, expansión y pasos con su etiqueta de nodo.

Pipeline por proyecto:
1. Cada archivo se trocea en sentencias (`split_statements`) y en nodos por etiqueta (`split_nodes`).
2. Se indexan todas las macros del proyecto antes de expandir nada, así una llamada puede usar una
   macro definida en otro archivo.
3. Se expande cada archivo. Los fragmentos dinámicos se separan como `MacroDynamic`; el resto se agrupa
   en pasos (`parse_steps`).
4. Cada paso y cada fragmento dinámico lleva la etiqueta del nodo en el que cae su línea.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.frontend.lexer import Stmt, split_statements
from sgm.frontend.macros import Expander, MacroDynamic, MacroIndex, index_file
from sgm.frontend.splitter import ZERO_WIDTH, Node, split_nodes
from sgm.frontend.steps import Unparsed, parse_steps


@dataclass
class ProgramItem:
    file: str
    label: str | None
    item: object  # paso (steps.*) o MacroDynamic
    line: int


@dataclass
class ProgramAnalysis:
    items: list[ProgramItem] = field(default_factory=list)
    index: MacroIndex = field(default_factory=MacroIndex)
    unresolved_includes: list[tuple[str, str, str]] = field(default_factory=list)
    nodes: dict[str, list[Node]] = field(default_factory=dict)

    @property
    def dynamics(self) -> list[ProgramItem]:
        return [i for i in self.items if isinstance(i.item, MacroDynamic)]

    @property
    def unparsed(self) -> list[ProgramItem]:
        return [i for i in self.items if isinstance(i.item, Unparsed)]


def _label_at(nodes: list[Node], line: int) -> str | None:
    """Etiqueta del nodo que contiene `line` (el último nodo que empieza en o antes de esa línea)."""
    found = None
    for node in nodes:
        if node.line_start > line:
            break
        found = node.label
    return found


def _collect(path: str, nodes: list[Node], expanded: list[object], result: ProgramAnalysis) -> None:
    """Agrupa los elementos expandidos en pasos y añade cada uno con su etiqueta de nodo."""
    pending: list[object] = []

    def flush_pending() -> None:
        steps, _ = parse_steps(pending)
        for step in steps:
            line = getattr(step, "line", 1)
            result.items.append(ProgramItem(path, _label_at(nodes, line), step, line))
        pending.clear()

    for item in expanded:
        if isinstance(item, MacroDynamic):
            flush_pending()
            result.items.append(ProgramItem(path, _label_at(nodes, item.line), item, item.line))
        else:
            pending.append(item)
    flush_pending()


def analyze_program(files: dict[str, str]) -> ProgramAnalysis:
    """Analiza un proyecto completo. `files` es {ruta relativa: texto}."""
    result = ProgramAnalysis()
    file_stmts: dict[str, list[Stmt]] = {}
    for path in sorted(files):
        text = files[path].replace(ZERO_WIDTH, "")
        file_stmts[path] = split_statements(text)
        result.nodes[path] = split_nodes(text)
    for path in sorted(files):
        index_file(path, file_stmts[path], result.index)
    expander = Expander(result.index, file_stmts)
    for path in sorted(files):
        _collect(path, result.nodes[path], expander.expand_file(path), result)
    result.unresolved_includes = list(expander.unresolved_includes)
    return result
