"""División del programa en nodos de SAS Studio por la línea `/* Etiqueta: <texto> */`.

Cada nodo conserva su etiqueta y las líneas de inicio y fin en el archivo original. El texto antes de
la primera etiqueta es un nodo sin etiqueta (`label=None`), y solo se emite si tiene contenido.
El carácter de ancho cero (U+200B) que SAS Studio añade al exportar se quita antes de dividir; no
cambia el número de línea.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ZERO_WIDTH = "​"
_LABEL = re.compile(r"^[ \t]*/\*[ \t]*Etiqueta:[ \t]*(.*?)[ \t]*\*/[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class Node:
    label: str | None
    text: str
    line_start: int
    line_end: int


def split_nodes(source: str) -> list[Node]:
    """Nodos del programa, en orden de aparición. El número de líneas se conserva."""
    text = source.replace(ZERO_WIDTH, "")
    labels = list(_LABEL.finditer(text))
    nodes: list[Node] = []
    if not labels:
        return [_node(None, text, 0, len(text), text)] if text.strip() else []
    head = text[: labels[0].start()]
    if head.strip():
        nodes.append(_node(None, text, 0, labels[0].start(), head))
    for index, match in enumerate(labels):
        end = labels[index + 1].start() if index + 1 < len(labels) else len(text)
        body = text[match.end(): end]
        nodes.append(_node(match.group(1).strip(), text, match.start(), end, body))
    return nodes


def _node(label: str | None, whole: str, start: int, end: int, body: str) -> Node:
    """Nodo con sus líneas (1-based, inclusive) según el rango `start:end` del texto completo."""
    first_line = whole.count("\n", 0, start) + 1
    last_line = whole.count("\n", 0, max(start, end - 1)) + 1
    return Node(label=label, text=body, line_start=first_line, line_end=last_line)
