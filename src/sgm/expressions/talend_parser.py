"""Analizador del traductor de Talend: convierte tokens SAS en expresiones Java con rutinas."""

import re

from sgm.expressions.talend_base import (
    _CMP,
    _FORMAT_ARGS,
    E,
    Unsupported,
    _compare,
    _guard,
    _jstr,
    _num,
    _str,
    _truth,
)
from sgm.expressions.talend_tabla import _FUNCTIONS

_MACRO_TRIGGER = re.compile(r"&+[A-Za-z_]\w*|%[A-Za-z_]\w*\s*\(")


class _P:
    def __init__(self, tokens: list[tuple[str, str]], entrada: str = "input_row"):
        self.t, self.i = tokens, 0
        self.entrada = entrada
        self.cols: list[str] = []
        self.warnings: set[str] = set()
        self.functions: set[str] = set()

    def peek(self, offset: int = 0) -> tuple[str, str]:
        j = self.i + offset
        return self.t[j] if j < len(self.t) else ("end", "")

    def take(self) -> tuple[str, str]:
        tok = self.peek()
        self.i += 1
        return tok

    def word(self, w: str, offset: int = 0) -> bool:
        k, v = self.peek(offset)
        return k == "id" and v.lower() == w

    def expect(self, value: str) -> None:
        if self.take()[1] != value:
            raise Unsupported(f"se esperaba {value!r}")

    # ---- lógica
    def expr(self) -> E:
        left = self.and_()
        while self.word("or") or self.peek()[1] in ("|", "!"):
            self.take()
            left = E(f"({_truth(left)} || {_truth(self.and_())})", "bool")
        return left

    def and_(self) -> E:
        left = self.not_()
        while self.word("and") or self.peek()[1] == "&":
            self.take()
            left = E(f"({_truth(left)} && {_truth(self.not_())})", "bool")
        return left

    def not_(self) -> E:
        if self.word("not") or self.peek()[1] in ("^", "~", "¬"):
            self.take()
            return E(f"(!{_truth(self.not_())})", "bool")
        return self.cmp()

    # ---- comparaciones
    def cmp(self) -> E:
        left = self.add()
        k, v = self.peek()
        low = v.lower()
        if k == "id" and low == "is":
            self.take()
            negate = self.word("not")
            if negate:
                self.take()
            if self.take()[1].lower() not in ("missing", "null"):
                raise Unsupported("IS sin MISSING/NULL")
            return E(f"{'!' if negate else ''}Relational.ISNULL({left.java})", "bool")
        negate = False
        if k == "id" and low == "not" and self.peek(1)[1].lower() in ("in", "between", "like"):
            self.take()
            negate = True
            k, v = self.peek()
            low = v.lower()
        if k == "id" and low == "in":
            self.take()
            self.expect("(")
            values = [self.add()]
            while self.peek()[1] == ",":
                self.take()
                values.append(self.add())
            self.expect(")")
            core = "(" + " || ".join(_compare("eq", left, x).java for x in values) + ")"
            return E(f"(!{core})" if negate else core, "bool")
        if k == "id" and low == "between":
            self.take()
            lo = self.add()
            if not self.word("and"):
                raise Unsupported("BETWEEN sin AND")
            self.take()
            hi = self.add()
            core = f"({_compare('ge', left, lo).java} && {_compare('le', left, hi).java})"
            return E(f"(!{core})" if negate else core, "bool")
        if k == "id" and low == "like":
            self.take()
            pattern = self.add()
            if pattern.kind != "str" or pattern.literal is None:
                raise Unsupported("LIKE con un patrón que no es literal")
            if any(not char.isprintable() for char in pattern.literal):
                raise Unsupported("LIKE con un patrón que contiene caracteres de control")
            regex = "".join(
                ".*" if char == "%" else "." if char == "_" else re.escape(char)
                for char in pattern.literal
            )
            regex = _jstr("'" + regex.replace("'", "''") + "'")
            core = f"({left.java} != null && {left.java}.matches({regex}))"
            return E(f"(!{core})" if negate else core, "bool")
        op = _CMP.get(low) if k in ("op", "id") else None
        if op is None:
            return left
        self.take()
        return _compare(op, left, self.add())

    # ---- aritmética
    def add(self) -> E:
        left = self.mul()
        while self.peek()[1] in ("+", "-", "||", "!!"):
            op = self.take()[1]
            right = self.mul()
            if op in ("||", "!!"):
                left = E(f"({_str(left)} + {_str(right)})", "str")
            else:
                left = self.arith(op, left, right)
        return left

    def mul(self) -> E:
        left = self.pow()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            left = self.arith(op, left, self.pow())
        return left

    def arith(self, op: str, a: E, b: E) -> E:
        expr = f"{_num(a)} {op} {_num(b)}"
        if a.kind == b.kind == "num":
            return E(f"({expr})", "num")
        guard = [a, b]
        body = f"Double.valueOf({expr})"
        # En SAS no hay aritmética de texto: el resultado de + - * / ** es siempre numérico, aunque no sepamos el
        # tipo de las columnas.
        if op == "/":  # dividir por cero es perdido en SAS
            return E(f"({_guard(guard, f'({_num(b)} == 0 ? null : {body})')})", "num")
        return E(_guard(guard, body), "num")

    def pow(self) -> E:
        base = self.unary()
        if self.peek()[1] == "**":
            self.take()
            exponent = self.pow()
            return E(
                _guard(
                    [base, exponent], f"Double.valueOf(Math.pow({_num(base)}, {_num(exponent)}))"
                )
            )
        return base

    def unary(self) -> E:
        if self.peek()[1] == "-":
            self.take()
            inner = self.unary()
            return (
                E(f"-{inner.java}", "num")
                if inner.kind == "num"
                else E(_guard([inner], f"Double.valueOf(-{_num(inner)})"))
            )
        if self.peek()[1] == "+":
            self.take()
            return self.unary()
        return self.atom()

    # ---- átomos
    def atom(self) -> E:
        k, v = self.take()
        if k == "str":
            literal = v[1:-1].replace(v[0] * 2, v[0])
            return E(_jstr(v), "str", literal)
        if k == "datelit":
            return E(f'TalendDate.parseDateLocale("ddMMMyyyy", "{v[1:-2]}", "en")', "date")
        if k == "num":
            return E(v if re.search(r"[.eE]", v) else v + ".0" if False else v, "num")
        if k == "fmt":
            return E(_jstr(f"'{v}'"), "str", v)
        if k == "mvar":
            name = v.lstrip("&").rstrip(".")
            self.warnings.add(
                f"Macrovariable &{name} -> context.sas_param_{name} (crear la variable de contexto)"
            )
            return E(f"context.sas_param_{name}")
        if k == "name":
            return self.column(re.search(r"'([^']+)'[nN]$", v).group(1))
        if k == "op" and v == ".":
            return E("null", "null")
        if k == "op" and v == "(":
            inner = self.expr()
            self.expect(")")
            return E(f"({inner.java})", inner.kind)
        if k == "id":
            low = v.lower()
            if low == "case":
                return self.case()
            if low == "calculated":
                return self.atom()
            if self.peek()[1] == "(" and low not in ("and", "or", "not", "in"):
                return self.call(low)
            if low in ("and", "or", "not", "in", "is", "then", "else", "end", "when"):
                raise Unsupported(f"palabra {v}")
            return self.column(v.split(".")[-1])
        raise Unsupported(f"inesperado: {v!r}")

    def column(self, name: str) -> E:
        self.cols.append(name)
        return E(f"{self.entrada}.{name}")

    def case(self) -> E:
        branches: list[tuple[E, E]] = []
        operand = None if self.word("when") else self.add()
        while self.word("when"):
            self.take()
            cond = self.expr() if operand is None else _compare("eq", operand, self.add())
            if not self.word("then"):
                raise Unsupported("CASE sin THEN")
            self.take()
            branches.append((cond, self.expr()))
        other = E("null", "null")
        if self.word("else"):
            self.take()
            other = self.expr()
        if not self.word("end"):
            raise Unsupported("CASE sin END")
        self.take()
        out = other
        for cond, value in reversed(branches):
            out = E(f"({_truth(cond)} ? {value.java} : {out.java})")
        return out

    # ---- funciones
    def call(self, name: str) -> E:
        self.take()  # (
        args: list[E] = []
        if self.peek()[1] != ")":
            while True:
                if name == "compress" and len(args) == 1 and self.peek()[1] == ",":
                    args.append(E("", "omitted"))
                else:
                    args.append(
                        self.raw_format() if name in _FORMAT_ARGS and len(args) == 1 else self.expr()
                    )
                if self.peek()[1] != ",":
                    break
                self.take()
        self.expect(")")
        builder = _FUNCTIONS.get(name)
        if builder is None:
            raise Unsupported(f"función {name}")
        self.functions.add(name)
        return builder(self, args)

    def raw_format(self) -> E:
        """El formato de `input`/`put` (`date9.`, `$10.`, `8.`) es un nombre, no una expresión."""
        kind, value = self.peek()
        literal = kind in ("fmt", "str") or (
            kind == "num" and re.fullmatch(r"\d+\.\d*", value) is not None
        )
        unresolved = kind == "str" and value.startswith('"') and _MACRO_TRIGGER.search(value)
        if not literal or unresolved or self.peek(1)[1] not in (",", ")"):
            raise Unsupported("informat dinámico o no literal; queda pendiente de resolución")
        self.take()
        if kind == "str":
            quote = value[0]
            value = value[1:-1].replace(quote * 2, quote)
        return E(_jstr("'" + value.replace("'", "''") + "'"), "str", value)
