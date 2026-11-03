"""Llamadas a macros y `%include` del expansor (mezcla de `Expander`)."""

from __future__ import annotations

import re

from sgm.frontend.lexer import Stmt
from sgm.frontend.macro_index import PathMatch, resolve_path
from sgm.frontend.macros_modelo import (  # noqa: E402
    _INCLUDE_PATH,
    _KEYWORD_ARG,
    MAX_DEPTH,
    Expanded,
    split_top,
)
from sgm.frontend.selectors import SelectorUse


class LlamadasMixin:
    def _call(self, call: re.Match, s: Stmt, env: dict, depth: int, file: str) -> list[object]:
        entry = self.index.get(call.group(1))
        assert entry is not None
        if depth >= MAX_DEPTH:
            return [self._dynamic(s, f"recursión de macros al llamar %{entry.name}")]
        selector = self.selectors.get(entry.name.lower())
        if selector is not None:
            # Un selector de ambiente no se expande: sus ramas son contextos (grupo del Job).
            self.selector_uses.append(SelectorUse(file, s.line, selector))
            return [Expanded(entry.name, f"{s.line}:{entry.name}", [])]
        args = split_top(call.group(2) or "")
        keywords = {}
        positional = []
        for arg in args:
            kw = _KEYWORD_ARG.match(arg)
            if kw and kw.group(1).lower() in {p.lower() for p, _ in entry.params}:
                keywords[kw.group(1).lower()] = kw.group(2).strip()
            else:
                positional.append(arg.strip())
        local = dict(env)
        for idx, (pname, default) in enumerate(entry.params):
            key = pname.lower()
            if key in keywords:
                raw = keywords[key]
            elif idx < len(positional):
                raw = positional[idx]
            else:
                raw = default
            if raw is None:
                local[key] = None
                continue
            value = self._subst(raw, env)
            local[key] = None if ("&" in value or "%" in value) else value
        self.trace.append(entry.name)
        items, _ = self._block(entry.body, 0, entry.file, local, depth + 1, nested=False)
        return [Expanded(entry.name, f"{s.line}:{entry.name}", items)]

    def _include(self, s: Stmt, file: str, env: dict, depth: int) -> list[object]:
        found = _INCLUDE_PATH.search(s.text)
        raw = found.group(1) if found else s.text.strip()[len("%include") :].strip()
        target = self._subst(raw, env)
        if "&" in target or "%" in target:
            self.unresolved_includes.append((file, raw, "dinámico"))
            return [s]
        match = resolve_path(target, self.paths)
        if match.status == "candidate" and match.file in self.externals:
            # Un archivo de env/externals con ese nombre: basta con el nombre para enlazarlo.
            match = PathMatch("resolved", match.file)
        if match.status != "resolved" or match.file is None or depth >= MAX_DEPTH:
            self.unresolved_includes.append((file, raw, match.status))
            return [s]
        items, _ = self._block(self.files[match.file], 0, match.file, env, depth + 1, nested=False)
        return items
