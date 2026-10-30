"""Divisor de sentencias SAS con números de línea. No ejecuta ni expande nada.

Quita comentarios (`/* */`, `* ...;`, `%* ...;`), respeta cadenas y `%str(...;...)`,
salta bloques `datalines`/`cards` y corta llamadas de macro `%nombre(...)` sin `;`.
"""

import re
from dataclasses import dataclass

# Palabras clave de macro que NO son llamadas a macros de usuario.
MACRO_KEYWORDS = frozenset(
    [
        "let",
        "put",
        "if",
        "then",
        "else",
        "do",
        "end",
        "to",
        "by",
        "until",
        "while",
        "macro",
        "mend",
        "include",
        "global",
        "local",
        "sysfunc",
        "qsysfunc",
        "str",
        "nrstr",
        "eval",
        "sysevalf",
        "symdel",
        "abort",
        "return",
        "goto",
        "label",
        "window",
        "display",
        "input",
        "sysexec",
        "list",
        "copy",
        "run",
        "cms",
        "bquote",
        "nrbquote",
        "quote",
        "nrquote",
        "unquote",
        "superq",
        "scan",
        "qscan",
        "substr",
        "qsubstr",
        "upcase",
        "qupcase",
        "lowcase",
        "index",
        "length",
        "sysget",
        "symexist",
        "sysmacexist",
        "sysrc",
        "syscall",
    ]
)
_CALL = re.compile(r"%([A-Za-z_]\w*)\s*\(")
_QUOTING = re.compile(r"%(?:nr)?str\(|%n?r?bquote\(", re.IGNORECASE)
_DATALINES = re.compile(r"^(datalines|cards)(4?)$", re.IGNORECASE)


@dataclass(frozen=True)
class Stmt:
    text: str  # sin comentarios, recortado
    line: int
    end_line: int
    rows: tuple[str, ...] = ()  # filas de un bloque `datalines`/`cards`, tal cual venían


def _skip_string(src: str, i: int) -> int:
    """Índice tras la cadena que abre en src[i]; i+1 si no cierra (comilla suelta)."""
    j = src.find(src[i], i + 1)
    return i + 1 if j < 0 else j + 1


def _call_end(src: str, i: int) -> int:
    """Índice tras el ')' que cierra el '(' de src[i:] (balanceado, con cadenas)."""
    depth = 0
    while i < len(src):
        c = src[i]
        if c in "'\"":
            i = _skip_string(src, i)
            continue
        depth += c == "("
        depth -= c == ")"
        i += 1
        if depth == 0:
            return i
    return i


def split_statements(src: str) -> list[Stmt]:
    out: list[Stmt] = []
    buf: list[str] = []
    start = 0
    line = 1
    i, n = 0, len(src)
    qdepth = 0  # dentro de %str(...)

    def emit(end_line: int) -> None:
        nonlocal buf, start
        text = "".join(buf).strip()
        if text:
            out.append(Stmt(text, start, end_line))
        buf, start = [], 0

    def add(chunk: str) -> None:
        nonlocal start, line
        if not start and chunk.strip():
            start = line
        buf.append(chunk)
        line += chunk.count("\n")

    while i < n:
        c = src[i]
        if qdepth:
            qdepth += c == "("
            qdepth -= c == ")"
            add(c)
            i += 1
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            line += src.count("\n", i, j)
            buf.append(" ")
            i = j
            continue
        at_start = not start
        if at_start and (c == "*" or src.startswith("%*", i)):
            j = src.find(";", i)
            j = n if j < 0 else j + 1
            line += src.count("\n", i, j)
            i = j
            continue
        if at_start and c == "%":
            m = _CALL.match(src, i)
            if m and m.group(1).lower() not in MACRO_KEYWORDS:
                j = _call_end(src, m.end() - 1)
                add(src[i:j])
                emit(line)
                k = j
                while k < n and src[k] in " \t\r\n":
                    k += 1
                if k < n and src[k] == ";":
                    line += src.count("\n", j, k + 1)
                    i = k + 1
                else:
                    i = j
                continue
        if c == "%":
            m = _QUOTING.match(src, i)
            if m:
                add(m.group())
                qdepth = 1
                i = m.end()
                continue
        if c in "'\"":
            j = _skip_string(src, i)
            add(src[i:j])
            i = j
            continue
        if c == ";":
            end_line = line
            emit(end_line)
            i += 1
            m = _DATALINES.match(out[-1].text) if out and out[-1].end_line == end_line else None
            if m:
                term = ";;;;" if m.group(2) else ";"
                first = line
                rows: list[str] = []
                # El resto de la línea de `datalines;` no es una fila si solo tiene espacios.
                eol = src.find("\n", i)
                if eol >= 0 and not src[i:eol].strip():
                    line += 1
                    i = eol + 1
                while i < n:
                    j = src.find("\n", i)
                    j = n if j < 0 else j
                    row = src[i:j].strip()
                    line += 1 if j < n else 0
                    i = j + 1
                    if row == term or (not m.group(2) and row.startswith(";")):
                        break
                    rows.append(row)
                out.append(Stmt("<datalines>", first, line, tuple(rows)))
            continue
        add(c)
        i += 1
    emit(line)
    return out
