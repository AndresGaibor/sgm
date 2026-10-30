"""Utilidades de macros que no dependen del AST: sustitución de `&var`, comillas y casado de `%include`.

Porte parcial del resolvedor anterior. Se conservan las funciones puras. El índice de macros
(`%macro ... %mend`) y las constantes `%let` se reescriben en el hito 4 sobre los pasos nuevos.
No expande macros. Lo que no se puede resolver con certeza queda sin resolver (nunca se adivina).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

_VAR = re.compile(r"&([A-Za-z_]\w*)\.?")
_QUOTED = re.compile(r"""^\s*(['"])(.*?)\1""", re.DOTALL)


def substitute(text: str, variables: dict[str, str]) -> tuple[str, bool]:
    """Sustituye `&var`/`&var.` conocidas. Devuelve (texto, completo)."""
    complete = "&&" not in text

    def rep(m: re.Match) -> str:
        nonlocal complete
        v = variables.get(m.group(1).lower())
        if v is None:
            complete = False
            return m.group(0)
        return v

    res = _VAR.sub(rep, text)
    return res, complete and "&" not in res


def first_quoted(s: str) -> str | None:
    m = _QUOTED.match(s)
    return m.group(2) if m else None


@dataclass(frozen=True)
class PathMatch:
    status: str  # resolved | candidate | ambiguous | external
    file: str | None = None


class PathIndex:
    """Archivos del proyecto indexados por nombre (minúsculas): evita recorrerlos todos por cada ruta."""

    def __init__(self, files: Iterable[str]):
        self.by_name: dict[str, list[tuple[str, list[str]]]] = {}
        for f in files:
            parts = [c.lower() for c in PurePosixPath(f).parts]
            if parts:
                self.by_name.setdefault(parts[-1], []).append((f, parts))


def resolve_path(raw: str, files: Iterable[str] | PathIndex) -> PathMatch:
    """Casa una ruta de `%include`/programa con un archivo del proyecto por sufijo de ruta.

    resolved: coinciden ≥2 componentes (o todos los de una ruta corta).
    candidate: solo coincide el nombre de archivo (no se enlaza; se informa).
    """
    want = [c.lower() for c in PurePosixPath(raw.replace("\\", "/")).parts if c not in ("/", ".")]
    if not want:
        return PathMatch("external")
    index = files if isinstance(files, PathIndex) else PathIndex(files)
    best, best_len, tie = None, 0, False
    for f, have in index.by_name.get(want[-1], ()):
        n = 0
        while n < min(len(want), len(have)) and want[-1 - n] == have[-1 - n]:
            n += 1
        if n > best_len:
            best, best_len, tie = f, n, False
        elif n == best_len and n > 0:
            tie = True
    if not best_len:
        return PathMatch("external")
    if tie:
        return PathMatch("ambiguous")
    if best_len >= 2 or len(want) == 1 or best_len == len(want):
        return PathMatch("resolved", best)
    return PathMatch("candidate", best)
