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
from sgm.frontend.macros import Expanded, Expander, MacroDynamic, MacroIndex, index_file
from sgm.frontend.selectors import SelectorUse
from sgm.frontend.splitter import ZERO_WIDTH, Node, split_nodes
from sgm.frontend.steps import Unparsed, parse_steps


@dataclass
class ProgramItem:
    file: str
    label: str | None
    item: object  # paso (steps.*) o MacroDynamic
    line: int
    call: str | None = (
        None  # invocación de macro más interna de la que sale el paso, "línea:nombre"
    )
    outer_call: str | None = None  # invocación más externa (la del código que escribió el usuario)


@dataclass
class ProgramAnalysis:
    items: list[ProgramItem] = field(default_factory=list)
    index: MacroIndex = field(default_factory=MacroIndex)
    unresolved_includes: list[tuple[str, str, str]] = field(default_factory=list)
    nodes: dict[str, list[Node]] = field(default_factory=dict)
    selector_uses: list[SelectorUse] = field(default_factory=list)  # macros de ambiente invocadas

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


def _flatten(items: list[object], call: str | None = None, outer: str | None = None):
    """Aplana las expansiones; cada sentencia conserva su invocación más interna y la más externa."""
    for item in items:
        if isinstance(item, Expanded):
            # la invocación más interna identifica el bloque; la más externa, dónde se llamó
            yield from _flatten(item.items, item.key, outer or item.key)
        else:
            yield item, call, outer


def _collect(path: str, nodes: list[Node], expanded: list[object], result: ProgramAnalysis) -> None:
    """Agrupa los elementos expandidos en pasos y añade cada uno con su etiqueta de nodo y su llamada."""
    pending: list[object] = []
    pending_call: str | None = None
    pending_outer: str | None = None

    def flush_pending(call: str | None, outer: str | None) -> None:
        steps, _ = parse_steps(pending)
        for step in steps:
            line = getattr(step, "line", 1)
            result.items.append(
                ProgramItem(path, _label_at(nodes, line), step, line, call, outer)
            )
        pending.clear()

    for item, call, outer in _flatten(expanded):
        if isinstance(item, MacroDynamic):
            flush_pending(pending_call, pending_outer)
            result.items.append(
                ProgramItem(path, _label_at(nodes, item.line), item, item.line, call, outer)
            )
            pending_call = None
            pending_outer = None
            continue
        if pending and (call != pending_call or outer != pending_outer):
            flush_pending(pending_call, pending_outer)
        pending_call = call
        pending_outer = outer
        pending.append(item)
    flush_pending(pending_call, pending_outer)


def analyze_program(
    files: dict[str, str], external_files: dict[str, str] | None = None
) -> ProgramAnalysis:
    """Analiza un proyecto completo. `files` es {ruta relativa: texto}.

    `external_files` son archivos de `env/externals/`: sirven para expandir `%include` y sus macros
    se indexan, pero no son programas: no generan pasos ni guía propia.
    """
    result = ProgramAnalysis()
    extras = external_files or {}
    everything = {**extras, **files}
    file_stmts: dict[str, list[Stmt]] = {}
    for path in sorted(everything):
        text = everything[path].replace(ZERO_WIDTH, "")
        file_stmts[path] = split_statements(text)
        if path in files:
            result.nodes[path] = split_nodes(text)
    for path in sorted(everything):
        index_file(path, file_stmts[path], result.index)
    expander = Expander(result.index, file_stmts, externals=frozenset(extras))
    for path in sorted(files):
        _collect(path, result.nodes[path], expander.expand_file(path), result)
    result.unresolved_includes = list(expander.unresolved_includes)
    result.selector_uses = list(expander.selector_uses)
    return result
