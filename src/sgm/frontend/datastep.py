"""Árbol del DATA step: encabezado (salidas) y sentencias clasificadas.

Reconoce `set`, `merge` con `in=`, `by`, `where`, asignaciones, `if/then/else`, `output`, `keep`, `drop`,
`rename`, `retain`, `lag`, `first.`/`last.`, `array`, `do`/`end`, `infile`, `input`, `datalines` y
`call symput`. Lo demás queda como `other` con su texto: nunca se pierde una sentencia.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sgm.frontend.datastep_io import infile_fields, input_fields

_DATA_HEADER = re.compile(r"(?is)^data\s+(.*)$")
_OUTPUT_NAME = re.compile(r"([A-Za-z_&][\w.&]*)\s*(\([^)]*\))?")
_SOURCE = re.compile(r"([A-Za-z_&][\w.&]*)\s*(\(([^)]*)\))?")
_ASSIGN = re.compile(r"^([A-Za-z_][\w.]*(?:\s*\([^)]*\))?)\s*=\s*(.+)$", re.DOTALL)
_LAG = re.compile(r"\blag\d*\s*\(", re.IGNORECASE)
_FIRST_LAST = re.compile(r"\b(first|last)\.(\w+)", re.IGNORECASE)
_SYMPUT = re.compile(r"(?i)^call\s+symputx?\s*\(\s*['\"]?(\w+)['\"]?")
_IN_OPTION = re.compile(r"(?i)\bin\s*=\s*(\w+)")
_RENAME_PAIR = re.compile(r"([\w&]+)\s*=\s*([\w&]+)")


@dataclass(frozen=True)
class DsStatement:
    kind: str
    text: str
    line: int
    fields: dict = field(default_factory=dict)
    file: str | None = None
    end_line: int | None = None


@dataclass
class DataStep:
    outputs: list[str]
    statements: list[DsStatement]
    line: int
    end_line: int
    text: str


def parse_data_header(body: str) -> list[str] | None:
    """Nombres de las salidas de `data a b(keep=...);`. None si el encabezado no tiene ninguna."""
    m = _DATA_HEADER.match(body.strip())
    if not m:
        return None
    names = [name for name, _ in _OUTPUT_NAME.findall(m.group(1))]
    return names or None


def _names(text: str) -> list[str]:
    return [name for name, _, _ in _SOURCE.findall(text)]


def _dataset_refs(text: str) -> list[dict]:
    """Datasets de `set`/`merge` con sus opciones; `in=` se guarda como variable indicadora."""
    refs = []
    position = 0
    while position < len(text):
        match = re.search(r"[A-Za-z_&][\w.&]*", text[position:])
        if match is None:
            break
        start = position + match.start()
        name = match.group(0)
        position = start + len(name)
        while position < len(text) and text[position].isspace():
            position += 1
        opts = ""
        if position < len(text) and text[position] == "(":
            inicio = position
            depth = 0
            quote = ""
            while position < len(text):
                caracter = text[position]
                if quote:
                    if caracter == quote:
                        quote = ""
                elif caracter in "'\"":
                    quote = caracter
                elif caracter == "(":
                    depth += 1
                elif caracter == ")":
                    depth -= 1
                    if depth == 0:
                        position += 1
                        break
                position += 1
            opts = text[inicio + 1 : position - 1]
        in_match = _IN_OPTION.search(opts)
        ref = {"name": name, "options": opts, "in": in_match.group(1) if in_match else None}
        where = re.search(r"(?is)\bwhere\s*=\s*\((.*)\)\s*$", opts)
        if where:
            ref["where"] = where.group(1).strip()
        refs.append(ref)
    return refs


def classify_statement(text: str, line: int, rows: tuple[str, ...] = ()) -> DsStatement:
    """Clasifica una sentencia de DATA step (sin `;`)."""
    body = text.strip()
    low = body.lower()
    word = re.match(r"[a-z_]+", low)
    head = word.group(0) if word else ""
    if body == "<datalines>":
        return DsStatement("datalines", body, line, {"rows": len(rows), "data": list(rows)})
    # Un nombre de variable puede coincidir con una palabra de sentencia, por ejemplo
    # `label = ...` o `input = ...`; reconoce primero la forma inequívoca de asignación.
    if m := _ASSIGN.match(body):
        target, expression = m.group(1).strip(), m.group(2).strip()
        kind = "lag" if _LAG.search(expression) else "assign"
        return DsStatement(kind, body, line, {"target": target, "expression": expression})
    if head == "set":
        return DsStatement("set", body, line, {"sources": _dataset_refs(body[3:])})
    if head == "merge":
        return DsStatement("merge", body, line, {"sources": _dataset_refs(body[5:])})
    if head == "by":
        return DsStatement(
            "by", body, line, {"names": [n.strip() for n in body[2:].split() if n.strip()]}
        )
    if head == "where":
        return DsStatement("where", body, line, {"expression": body[5:].strip()})
    if head == "output":
        return DsStatement(
            "output", body, line, {"target": _names(body[6:])[0] if _names(body[6:]) else None}
        )
    if head in ("keep", "drop"):
        return DsStatement(head, body, line, {"names": _names(body[len(head) :])})
    if head == "rename":
        return DsStatement("rename", body, line, {"pairs": _RENAME_PAIR.findall(body[6:])})
    if head == "retain":
        return DsStatement("retain", body, line, {"names": _names(body[6:])})
    if head in ("format", "informat", "length", "label", "attrib"):
        return DsStatement("declare", body, line, {"declaration": head})
    if head == "array":
        return DsStatement("array", body, line, {})
    if head == "do":
        return DsStatement("do", body, line, {})
    if head == "end":
        return DsStatement("end", body, line, {})
    if head == "infile":
        return DsStatement("infile", body, line, infile_fields(body))
    if head == "input":
        return DsStatement("input", body, line, input_fields(body))
    if head in ("file", "put"):
        return DsStatement(head, body, line, {"raw": body})
    if head == "if" or head == "else":
        flags = [f"{kind}.{name}" for kind, name in _FIRST_LAST.findall(body)]
        return DsStatement("if", body, line, {"first_last": flags})
    if m := _SYMPUT.match(body):
        return DsStatement("call_symput", body, line, {"name": m.group(1)})
    return DsStatement("other", body, line)
