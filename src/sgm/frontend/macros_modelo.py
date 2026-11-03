"""Expansor de macros con evaluación parcial.

Trabaja sobre las sentencias crudas del lexer (no sobre pasos), porque `%if`, `%do` y `%let` cortan el
código de forma que solo se entiende con la secuencia completa. Resuelve lo constante: `%let` con valor
fijo, `&var` conocidas, `%if` y `%do` con condición o límites constantes, y llamadas a macros definidas.
Lo que depende de la ejecución (`call symput`, `%sysfunc` sobre datos, `into :var` en SQL, condiciones
o límites no constantes) se marca como `MacroDynamic` con motivo `MACRO_DINAMICA`.

Nunca se adivina: un valor desconocido queda como desconocido y el texto original se conserva.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from sgm.frontend.lexer import Stmt

MAX_DEPTH = 20
MAX_ITERATIONS = 1000
REASON = "MACRO_DINAMICA"

_CALL = re.compile(r"(?is)^%(\w+)\s*(?:\((.*)\))?\s*$")
_MACRO_HEAD = re.compile(r"(?is)^%macro\s+(\w+)\s*(?:\((.*)\))?\s*$")
_LET = re.compile(r"(?is)^%let\s+(\w+)\s*=\s*(.*)$")
_IF = re.compile(r"(?is)^%if\s+(.*?)\s+%then\b\s*(.*)$")
_DO_TO = re.compile(r"(?is)^%do\s+(\w+)\s*=\s*(.+?)\s+%to\s+(.+?)(?:\s+%by\s+(.+?))?\s*$")
_COMPARE = re.compile(r"(?i)^(.+?)\s*(=|eq|\^=|~=|ne|<>|>=|<=|>|<|gt|lt|ge|le)\s*(.+)$")
_DYNAMIC_FN = re.compile(r"(?i)%(sysfunc|qsysfunc|sysevalf|sysget|sysmacexist)\b")
_SYMPUT = re.compile(r"(?i)\bcall\s+symputx?\s*\(")
_INTO = re.compile(r"(?i)\binto\s*:")
_SQL_SELECT = re.compile(r"(?is)^\s*select\b")
_INT_EXPR = re.compile(r"^[\d\s+\-*/()]+$")
_KEYWORD_ARG = re.compile(r"^\s*(\w+)\s*=(.*)$", re.DOTALL)
_INCLUDE_PATH = re.compile(r"""['"]([^'"]+)['"]""")


@dataclass
class MacroDynamic:
    """Fragmento que depende de la ejecución; se conserva su texto y el motivo."""

    text: str
    detail: str
    line: int
    end_line: int
    reason: str = REASON


@dataclass
class Expanded:
    """Salida de una llamada de macro expandida. `key` identifica la invocación ("archivo:línea:nombre")."""

    name: str
    key: str
    items: list[object]


@dataclass
class MacroEntry:
    name: str
    params: list[tuple[str, str | None]]  # (nombre, valor por defecto o None)
    body: list[Stmt]
    file: str
    line: int
    key: str  # huella del cuerpo normalizado


@dataclass
class MacroIndex:
    entries: dict[str, list[MacroEntry]] = field(default_factory=dict)
    duplicates: int = 0  # definiciones idénticas (mismo cuerpo normalizado), contadas una vez
    conflicts: list[str] = field(default_factory=list)  # nombres definidos con cuerpos distintos

    def add(self, entry: MacroEntry) -> None:
        variants = self.entries.setdefault(entry.name.lower(), [])
        if any(v.key == entry.key for v in variants):
            self.duplicates += 1
            return
        if variants:
            self.conflicts.append(entry.name.lower())
        variants.append(entry)

    def get(self, name: str) -> MacroEntry | None:
        variants = self.entries.get(name.lower())
        return variants[0] if variants else None

    def __len__(self) -> int:
        return len(self.entries)


def split_top(text: str) -> list[str]:
    """Parte por comas que no están dentro de paréntesis ni de comillas."""
    parts, buf, depth, quote = [], [], 0, ""
    for ch in text:
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    parts.append("".join(buf))
    return [p for p in parts if p.strip()]


def _block_end(stmts: list[Stmt], i: int) -> int:
    """Índice del `%mend` que cierra el `%macro` de stmts[i] (con anidados). len si no hay cierre."""
    depth = 0
    for j in range(i, len(stmts)):
        low = stmts[j].text.strip().lower()
        if low.startswith("%macro"):
            depth += 1
        elif low.startswith("%mend"):
            depth -= 1
            if depth == 0:
                return j
    return len(stmts)


def _body_key(body: list[Stmt]) -> str:
    normalized = "\n".join(" ".join(s.text.lower().split()) for s in body)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def index_file(file: str, stmts: list[Stmt], index: MacroIndex) -> None:
    """Registra las definiciones `%macro ... %mend` de un archivo, también las anidadas."""
    i = 0
    while i < len(stmts):
        text = stmts[i].text.strip()
        if not text.lower().startswith("%macro"):
            i += 1
            continue
        end = _block_end(stmts, i)
        head = _MACRO_HEAD.match(text)
        if head:
            params = []
            for raw in split_top(head.group(2) or ""):
                name, eq, default = raw.partition("=")
                params.append((name.strip().lstrip("&"), default.strip() if eq else None))
            body = stmts[i + 1 : end]
            index.add(MacroEntry(head.group(1), params, body, file, stmts[i].line, _body_key(body)))
            index_file(file, body, index)
        i = end + 1


def _int(text: str) -> int | None:
    """Entero de un literal o de una expresión sencilla (%eval); None si no es constante."""
    expr = text.strip()
    if m := re.match(r"(?i)^%eval\s*\((.*)\)$", expr):
        expr = m.group(1)
    if not _INT_EXPR.match(expr):
        return int(expr) if re.fullmatch(r"[+-]?\d+", expr) else None
    try:
        value = eval(
            expr, {"__builtins__": {}}, {}
        )  # solo dígitos y operadores aritméticos (ver _INT_EXPR)
    except (SyntaxError, ZeroDivisionError):
        return None
    return int(value) if isinstance(value, (int, float)) else None


def _unquote(text: str) -> str:
    return text.strip().strip("'\"")
