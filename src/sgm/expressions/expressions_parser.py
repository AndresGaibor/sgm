"""Analizador de expresiones SAS: convierte tokens en una expresión Java conservadora."""

import re

from sgm.expressions.expressions_base import (
    _CMP,
    _FUNCS,
    _FUNCS_AVISO,
    _NUMBER,
    _TOKEN,
    _Unsupported,
)
from sgm.expressions.expressions_funciones import (
    _FUNCTION_WARNINGS,
    _FUNCTIONS,
    TEXT_TYPE_WARNING,
)


def _text_is(column: str, literal: str) -> str:
    """Igualdad null-safe de una columna con un literal de texto (SAS: ausente equivale a blanco)."""
    if literal == '""':
        return f"({column} == null || {column}.trim().isEmpty())"
    return f"{literal}.equals({column})"


def _tokens(s: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    s = s.strip()
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m or m.end() == pos:
            # Sin el fragmento en el mensaje: la expresión puede traer un secreto o un nombre de cliente.
            raise _Unsupported("token no soportado en la expresión; queda pendiente de revisión")
        kind = m.lastgroup or ""
        out.append((kind, m.group(kind)))
        pos = m.end()
    return out


class _Parser:
    def __init__(self, toks: list[tuple[str, str]]):
        self.t, self.i = toks, 0
        self.cols: list[str] = []
        self.warnings: list[str] = []
        self.simple: list[dict] = []
        self.ops: set[str] = set()
        self.unsafe_comparison = False

    def peek(self) -> tuple[str, str]:
        return self.t[self.i] if self.i < len(self.t) else ("end", "")

    def take(self) -> tuple[str, str]:
        tok = self.peek()
        self.i += 1
        return tok

    def is_word(self, w: str) -> bool:
        k, v = self.peek()
        return k == "id" and v.lower() == w

    # lógica
    def expr(self) -> str:
        left = self.and_()
        while self.is_word("or") or self.peek()[1] == "|":
            self.take()
            self.ops.add("||")
            left = f"({left} || {self.and_()})"
        return left

    def and_(self) -> str:
        left = self.not_()
        while self.is_word("and") or self.peek()[1] == "&":
            self.take()
            self.ops.add("&&")
            left = f"({left} && {self.not_()})"
        return left

    def not_(self) -> str:
        if self.is_word("not") or self.peek()[1] in ("^", "~"):
            self.take()
            self.ops.add("!")
            return f"!({self.not_()})"
        return self.cmp()

    def cmp(self) -> str:
        left_start = self.i
        left = self.arith()
        k, v = self.peek()
        op = _CMP.get(v.lower()) if k in ("op", "id") else None
        if self.is_word("in"):
            self.take()
            if self.take()[1] != "(":
                raise _Unsupported("IN sin paréntesis")
            vals = [self.arith()]
            while self.peek()[1] in (",",) or self.peek()[0] in ("str", "num"):
                if self.peek()[1] == ",":
                    self.take()
                vals.append(self.arith())
            if self.take()[1] != ")":
                raise _Unsupported("IN sin cierre")
            self.ops.add("in")
            if re.fullmatch(r"input_row\.\w+", left) and all(
                x.startswith('"') and not _NUMBER.fullmatch(x.strip('"')) for x in vals
            ):
                self.warnings.append(TEXT_TYPE_WARNING)
                return "(" + " || ".join(_text_is(left, x) for x in vals) + ")"
            if re.fullmatch(r"input_row\.\w+", left):
                self.unsafe_comparison = True
                self.warnings.append(
                    "IN sobre columna sin tipo conocido: validar conversión y semántica de missing/nulos"
                )
            return (
                "("
                + " || ".join(
                    f"{left}.equals({x})" if x.startswith('"') else f"{left} == {x}" for x in vals
                )
                + ")"
            )
        if op is None:
            return left
        self.take()
        right = self.arith()
        text_expr: str | None = None
        left_column = re.fullmatch(r"input_row\.\w+", left)
        right_column = re.fullmatch(r"input_row\.\w+", right)
        if left_column or right_column:
            other = right if left_column else left
            column = left if left_column else right
            if (
                op in ("==", "!=")
                and other.startswith('"')
                and not _NUMBER.fullmatch(other.strip('"'))
            ):
                # Igualdad con texto: la columna se asume texto; el paso se valida con el esquema real.
                self.warnings.append(TEXT_TYPE_WARNING)
                text_expr = _text_is(column, other)
                if op == "!=":
                    text_expr = f"!({text_expr})"
            elif _NUMBER.fullmatch(other) and op in ("<", ">", "<=", ">="):
                # Orden frente a un literal numérico: el tipo sale del literal (validar en Studio).
                # La igualdad no se infiere: sin tipo, una columna puede ser texto.
                self.warnings.append(
                    "tipo no confirmado: el tipo numérico se infiere del literal de la comparación; validar que la columna es numérica"
                )
            else:
                self.unsafe_comparison = True
                self.warnings.append(
                    "Comparación con columna sin tipo conocido: validar conversión, orden y semántica de missing/nulos"
                )
        if (
            len(self.t)
            and self.i - left_start == 3
            and self.t[left_start][0] == "id"
            and self.t[left_start + 2][0] in ("str", "num", "mvar")
        ):
            self.simple.append(
                {
                    "column": self.t[left_start][1],
                    "operator": op,
                    "value": self.t[left_start + 2][1],
                }
            )
        else:
            self.simple.append({})  # no representable en modo simple
        if text_expr is not None:
            return text_expr
        if op in ("<", "<=", "!="):
            self.warnings.append(
                "Missing numérico: en SAS es menor que cualquier número; en Java un null no compara igual"
            )
        if op in ("==", "!=") and (right.startswith('"') or left.startswith('"')):
            s, o = (right, left) if right.startswith('"') else (left, right)
            return f"{'!' if op == '!=' else ''}{o}.equals({s})"
        return f"({left} {op} {right})"

    def function(self, name: str, args: list[str]) -> str:
        """Llamada a función SAS con argumentos ya traducidos. Sin equivalente claro: `_Unsupported`."""
        if name in _FUNCS and len(args) == 1:
            self.warnings.append(f"{name}(): {_FUNCS_AVISO[name]}")
            return _FUNCS[name].format(args[0])
        handler = _FUNCTIONS.get(name)
        if handler is None:
            raise _Unsupported(f"función {name}")
        result = handler(args)
        self.warnings.extend(_FUNCTION_WARNINGS.get(name, []))
        return result

    # aritmética
    def arith(self) -> str:
        left = self.term()
        while self.peek()[1] in ("+", "-", "||"):
            op = self.take()[1]
            right = self.term()
            left = f"({left} {'+' if op == '||' else op} {right})"
        return left

    def term(self) -> str:
        left = self.atom()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            left = f"({left} {op} {self.atom()})"
        return left

    def atom(self) -> str:
        k, v = self.take()
        if k == "str":
            body = v[1:-1].replace(v[0] * 2, v[0]).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{body}"'
        if k == "num":
            return v
        if k == "fmt":
            return f'"{v}"'
        if k == "mvar":
            name = v.lstrip("&").rstrip(".")
            self.warnings.append(
                f"Macrovariable &{name} → context.{name} (crear variable de contexto)"
            )
            return f"context.{name}"
        if k == "op" and v == "(":
            e = self.expr()
            if self.take()[1] != ")":
                raise _Unsupported("paréntesis sin cerrar")
            return f"({e})"
        if k == "op" and v == "-":
            return f"-{self.atom()}"
        if k == "id":
            if self.peek()[1] == "(":
                name = v.lower()
                if name == "missing":
                    self.take()
                    arg = self.expr()
                    if self.take()[1] != ")":
                        raise _Unsupported("missing(")
                    self.warnings.append("missing(): null (y cadena vacía si es texto) en Java")
                    return f"({arg} == null)"
                self.take()  # "("
                args: list[str] = []
                if self.peek()[1] != ")":
                    args.append(self.expr())
                    while self.peek()[1] == ",":
                        self.take()
                        args.append(self.expr())
                if self.take()[1] != ")":
                    raise _Unsupported(f"{v}(")
                return self.function(name, args)
            if v == "." or v.lower() in ("and", "or", "not", "in"):
                raise _Unsupported(f"palabra {v}")
            col = v.split(".")[-1]
            self.cols.append(col)
            return f"input_row.{col}"
        raise _Unsupported(f"inesperado: {v!r}")
