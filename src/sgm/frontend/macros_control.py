"""Control de macros del expansor: condiciones (`%if`), ramas y bucles (`%do`).

Son métodos de `Expander` (mezcla): usan su estado y sus métodos de sustitución y de bloques.
"""

from __future__ import annotations

import re
from dataclasses import replace

from sgm.frontend.lexer import Stmt
from sgm.frontend.macros_modelo import (  # noqa: E402
    _COMPARE,
    _DO_TO,
    _IF,
    MAX_ITERATIONS,
    _int,
    _unquote,
)


class ControlMixin:
    def _condition(self, raw: str, env: dict) -> bool | None:
        text = self._subst(raw, env).strip()
        if "&" in text or "%" in text or re.search(r"(?i)\b(and|or|not|in)\b", text):
            return None
        m = _COMPARE.match(text)
        if not m:
            return None
        left, op, right = _unquote(m.group(1)), m.group(2).lower(), _unquote(m.group(3))
        a, b = _int(left), _int(right)
        if a is not None and b is not None:
            left, right = a, b
        else:
            left, right = left.lower(), right.lower()
        ops = {
            "=": lambda x, y: x == y,
            "eq": lambda x, y: x == y,
            "^=": lambda x, y: x != y,
            "~=": lambda x, y: x != y,
            "ne": lambda x, y: x != y,
            "<>": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            "gt": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            "lt": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "ge": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "le": lambda x, y: x <= y,
        }
        try:
            return bool(ops[op](left, right))
        except TypeError:
            return None

    def _branch(
        self, stmts: list[Stmt], i: int, rest: str, file: str, env: dict, depth: int
    ) -> tuple[list[object], int]:
        """Rama de `%if`/`%else` que empieza en stmts[i] con el texto `rest` tras %then/%else.

        Devuelve (salida, índice donde sigue el código). Un `%do` consume su `%end`.
        """
        low = rest.lower()
        if not rest:
            return [], i + 1
        if low == "%do":
            items, end = self._block(stmts, i + 1, file, env, depth, nested=True)
            return items, min(end + 1, len(stmts))
        if low.startswith("%if"):
            new = [replace(stmts[i], text=rest)] + stmts[i + 1 :]
            items, k = self._if(new, 0, file, env, depth)
            return items, i + k
        items, _ = self._block([replace(stmts[i], text=rest)], 0, file, env, depth, nested=False)
        return items, i + 1

    def _if(
        self, stmts: list[Stmt], i: int, file: str, env: dict, depth: int
    ) -> tuple[list[object], int]:
        s = stmts[i]
        m = _IF.match(s.text.strip())
        if not m:
            return [self._dynamic(s, "%if no reconocido")], i + 1
        cond, rest = m.group(1), m.group(2).strip()
        verdict = self._condition(cond, env)
        then_env, else_env = dict(env), dict(env)
        then_items, j = self._branch(stmts, i, rest, file, then_env, depth)
        else_items: list[object] = []
        if j < len(stmts) and stmts[j].text.strip().lower().startswith("%else"):
            erest = stmts[j].text.strip()[len("%else") :].strip()
            else_items, j = self._branch(stmts, j, erest, file, else_env, depth)
        if verdict is None:
            # Condición no constante: se marca, pero las dos ramas se expanden para no perder el código.
            # Las variables que alguna rama cambia quedan desconocidas.
            for key in set(then_env) | set(else_env) | set(env):
                if then_env.get(key) != env.get(key) or else_env.get(key) != env.get(key):
                    env[key] = None
            dyn = self._dynamic(s, f"condición no constante: {cond.strip()}")
            return [dyn, *then_items, *else_items], j
        chosen_env = then_env if verdict else else_env
        env.update(chosen_env)
        return (then_items if verdict else else_items), j

    def _do(
        self, stmts: list[Stmt], i: int, file: str, env: dict, depth: int
    ) -> tuple[list[object], int]:
        s = stmts[i]
        text = s.text.strip()
        if text.lower() == "%do":
            items, end = self._block(stmts, i + 1, file, env, depth, nested=True)
            return items, min(end + 1, len(stmts))
        m = _DO_TO.match(text)
        if not m:  # %do %while / %until: el cuerpo se muestra una vez
            items, end = self._block(stmts, i + 1, file, dict(env), depth, nested=True)
            dyn = self._dynamic(s, "%do con condición no constante: el cuerpo se muestra una vez")
            return [dyn, *items], min(end + 1, len(stmts))
        var = m.group(1).lower()
        lo = _int(self._subst(m.group(2), env))
        hi = _int(self._subst(m.group(3), env))
        step = _int(self._subst(m.group(4), env)) if m.group(4) else 1
        if lo is None or hi is None or not step:
            body_env = {**env, var: None}
            items, end = self._block(stmts, i + 1, file, body_env, depth, nested=True)
            dyn = self._dynamic(s, "%do con límites no constantes: el cuerpo se muestra una vez")
            return [dyn, *items], min(end + 1, len(stmts))
        values = range(lo, hi + 1, step) if step > 0 else range(lo, hi - 1, step)
        if len(values) > MAX_ITERATIONS:
            _, end = self._block(stmts, i + 1, file, dict(env), depth, nested=True)
            return [self._dynamic(s, f"%do con más de {MAX_ITERATIONS} iteraciones")], min(
                end + 1, len(stmts)
            )
        out: list[object] = []
        end = len(stmts)
        for value in values:
            loop_env = dict(env)
            loop_env[var] = str(value)
            items, end = self._block(stmts, i + 1, file, loop_env, depth, nested=True)
            out += items
            env[var] = str(value)
        if not values:
            _, end = self._block(stmts, i + 1, file, dict(env), depth, nested=True)
        return out, min(end + 1, len(stmts))
