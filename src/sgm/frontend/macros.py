"""Expansor de macros con evaluación parcial (núcleo; el control y las llamadas están en mezclas).

Trabaja sobre las sentencias crudas del lexer. Resuelve lo constante y marca lo dinámico como
`MacroDynamic` con motivo `MACRO_DINAMICA`. Nunca se adivina: lo desconocido se conserva.
"""

from __future__ import annotations

import re
from dataclasses import replace

from sgm.frontend.lexer import MACRO_KEYWORDS, Stmt
from sgm.frontend.macro_index import PathIndex, substitute
from sgm.frontend.macros_control import ControlMixin
from sgm.frontend.macros_llamadas import LlamadasMixin
from sgm.frontend.macros_modelo import (  # noqa: E402
    _CALL,
    _DYNAMIC_FN,
    _INTO,
    _LET,
    _SQL_SELECT,
    _SYMPUT,
    Expanded,
    MacroDynamic,
    MacroIndex,
    _block_end,
    _int,
    index_file,
)
from sgm.frontend.selectors import Selector, SelectorUse, detect

__all__ = ["Expanded", "Expander", "MacroDynamic", "MacroIndex", "index_file"]


class Expander(ControlMixin, LlamadasMixin):
    """Expande un proyecto archivo por archivo. Guarda lo dinámico y lo que no se pudo resolver."""

    def __init__(
        self,
        index: MacroIndex,
        files: dict[str, list[Stmt]],
        externals: frozenset[str] = frozenset(),
    ):
        self.index = index
        self.files = files
        self.paths = PathIndex(files.keys())
        self.externals = externals  # archivos de env/externals: se casan por nombre de archivo
        self.selectors = _selectors(index)  # macros de ambiente: sus ramas son contextos
        self.selector_uses: list[SelectorUse] = []
        self.dynamics: list[MacroDynamic] = []
        self.trace: list[str] = []
        self.unresolved_includes: list[tuple[str, str, str]] = []

    def expand_file(self, file: str) -> list[object]:
        items, _ = self._block(self.files[file], 0, file, {}, 0, nested=False)
        return items

    # --- utilidades -----------------------------------------------------

    def _dynamic(self, stmt: Stmt, detail: str) -> MacroDynamic:
        item = MacroDynamic(stmt.text.strip(), detail, stmt.line, stmt.end_line)
        self.dynamics.append(item)
        return item

    @staticmethod
    def _consts(env: dict[str, str | None]) -> dict[str, str]:
        return {k: v for k, v in env.items() if v is not None}

    def _subst(self, text: str, env: dict[str, str | None]) -> str:
        return substitute(text, self._consts(env))[0]

    # --- bloques --------------------------------------------------------

    def _block(
        self, stmts: list[Stmt], i: int, file: str, env: dict, depth: int, nested: bool
    ) -> tuple[list[object], int]:
        """Expande desde stmts[i]. Si `nested`, para en el `%end` o `%else` que cierra el bloque."""
        out: list[object] = []
        while i < len(stmts):
            s = stmts[i]
            low = s.text.strip().lower()
            if nested and (low.startswith("%end") or low.startswith("%else")):
                return out, i
            if low.startswith("%macro"):
                i = _block_end(stmts, i) + 1
                continue
            if low.startswith("%let"):
                out.append(self._let(s, env))
                i += 1
                continue
            if re.match(r"%if\b", low):
                items, i = self._if(stmts, i, file, env, depth)
                out += items
                continue
            if re.match(r"%do\b", low):
                items, i = self._do(stmts, i, file, env, depth)
                out += items
                continue
            if low.startswith("%include"):
                out += self._include(s, file, env, depth)
                i += 1
                continue
            call = _CALL.match(s.text.strip())
            if (
                call
                and call.group(1).lower() not in MACRO_KEYWORDS
                and self.index.get(call.group(1))
            ):
                out += self._call(call, s, env, depth, file)
                i += 1
                continue
            out += self._ordinary(s, env)
            i += 1
        return out, i

    # --- sentencias ------------------------------------------------------

    def _let(self, s: Stmt, env: dict) -> object:
        m = _LET.match(s.text.strip())
        if not m:
            return s
        name = m.group(1).lower()
        raw = m.group(2).strip()
        if _DYNAMIC_FN.search(raw):
            env[name] = None
            return self._dynamic(s, f"%let con %sysfunc o similar: {name}")
        value = self._subst(raw, env)
        if (ev := _eval_call(value)) is not None:
            value = str(ev)
        if "&" in value or "%" in value:
            env[name] = None
        else:
            env[name] = value
        return replace(s, text=f"%let {m.group(1)} = {value}")

    def _ordinary(self, s: Stmt, env: dict) -> list[object]:
        text = s.text
        if _SYMPUT.search(text):
            return [self._dynamic(s, "call symput: el valor se calcula al ejecutar")]
        if _INTO.search(text) and not _SQL_SELECT.match(text):
            # `select ... into :var` de PROC SQL lo traduce el lowering de SQL (set_variable).
            return [self._dynamic(s, "into :variable: el valor sale de los datos")]
        if _DYNAMIC_FN.search(text):
            return [self._dynamic(s, "%sysfunc sobre datos o valores de ejecución")]
        return [replace(s, text=self._subst(text, env))]


def _selectors(index: MacroIndex) -> dict[str, Selector]:
    """Macros del proyecto con forma de selector de ambiente, por nombre en minúsculas."""
    found: dict[str, Selector] = {}
    for name, variants in index.entries.items():
        for entry in variants:
            selector = detect(entry.name, entry.body)
            if selector is not None:
                found[name] = selector
    return found


def _eval_call(text: str) -> int | None:
    """Valor entero de un `%eval(...)` ya sustituido; None si el texto no es un %eval constante."""
    if re.match(r"(?i)^%eval\s*\(", text.strip()):
        return _int(text)
    return None
