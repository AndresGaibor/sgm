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
from dataclasses import dataclass, field, replace

from sgm.frontend.lexer import MACRO_KEYWORDS, Stmt
from sgm.frontend.macro_index import PathIndex, resolve_path, substitute

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


class Expander:
    """Expande un proyecto archivo por archivo. Guarda lo dinámico y lo que no se pudo resolver."""

    def __init__(self, index: MacroIndex, files: dict[str, list[Stmt]]):
        self.index = index
        self.files = files
        self.paths = PathIndex(files.keys())
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
                out += self._call(call, s, env, depth)
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
        if _INTO.search(text):
            return [self._dynamic(s, "into :variable: el valor sale de los datos")]
        if _DYNAMIC_FN.search(text):
            return [self._dynamic(s, "%sysfunc sobre datos o valores de ejecución")]
        return [replace(s, text=self._subst(text, env))]

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
            return [self._dynamic(s, f"condición no constante: {cond.strip()}")], j
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
        if not m:
            _, end = self._block(stmts, i + 1, file, dict(env), depth, nested=True)
            return [self._dynamic(s, "%do con condición no constante")], min(end + 1, len(stmts))
        var = m.group(1).lower()
        lo = _int(self._subst(m.group(2), env))
        hi = _int(self._subst(m.group(3), env))
        step = _int(self._subst(m.group(4), env)) if m.group(4) else 1
        if lo is None or hi is None or not step:
            _, end = self._block(stmts, i + 1, file, dict(env), depth, nested=True)
            return [self._dynamic(s, "%do con límites no constantes")], min(end + 1, len(stmts))
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

    def _call(self, call: re.Match, s: Stmt, env: dict, depth: int) -> list[object]:
        entry = self.index.get(call.group(1))
        assert entry is not None
        if depth >= MAX_DEPTH:
            return [self._dynamic(s, f"recursión de macros al llamar %{entry.name}")]
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
        return items

    def _include(self, s: Stmt, file: str, env: dict, depth: int) -> list[object]:
        found = _INCLUDE_PATH.search(s.text)
        raw = found.group(1) if found else s.text.strip()[len("%include") :].strip()
        target = self._subst(raw, env)
        if "&" in target or "%" in target:
            self.unresolved_includes.append((file, raw, "dinámico"))
            return [s]
        match = resolve_path(target, self.paths)
        if match.status != "resolved" or match.file is None or depth >= MAX_DEPTH:
            self.unresolved_includes.append((file, raw, match.status))
            return [s]
        items, _ = self._block(self.files[match.file], 0, match.file, env, depth + 1, nested=False)
        return items


def _eval_call(text: str) -> int | None:
    """Valor entero de un `%eval(...)` ya sustituido; None si el texto no es un %eval constante."""
    if re.match(r"(?i)^%eval\s*\(", text.strip()):
        return _int(text)
    return None
