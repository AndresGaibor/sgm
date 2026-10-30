"""Traductor de expresiones SAS a lo que Talend trae de fábrica, sin bibliotecas propias.

Talend guarda una expresión como Java dentro de `tMap` o del modo avanzado de `tFilterRow`. Este traductor emite solo:

- **Rutinas de sistema de Talend** disponibles en cualquier proyecto (`StringHandling`, `TalendDate`, `Mathematical`,
  `Relational`), con firmas leídas de la instalación de Studio 8.0.
- **Java nativo** (`Math`, `Objects`, `Number`, operadores) con las guardas de nulo necesarias.

No hay nada que instalar. El **valor perdido de SAS es `null`**: los operadores lo propagan como SAS (un perdido numérico es
menor que cualquier número; `a + .` es perdido). Lo que SAS hace distinto y Talend no tiene (`lag`, `retain`) lanza
`Unsupported` y queda como pendiente. Cuando el tipo de una columna no se conoce, solo se emiten comparaciones que no lo
necesitan (igualdad con un literal, nulos, `Comparable`); los cálculos exactos esperan al esquema.
"""

import re
from dataclasses import dataclass

#: Informatos y formatos de fecha de SAS → patrón de Java para `TalendDate`.
DATE_FORMATS = {
    "yymmdd10": "yyyy-MM-dd", "yymmdd8": "yy-MM-dd", "yymmddn8": "yyyyMMdd", "ddmmyy10": "dd/MM/yyyy",
    "ddmmyy8": "dd/MM/yy", "mmddyy10": "MM/dd/yyyy", "mmddyy8": "MM/dd/yy", "date9": "ddMMMyyyy",
    "date7": "ddMMMyy", "datetime20": "ddMMMyyyy:HH:mm:ss", "datetime19": "ddMMMyyyy:HH:mm:ss",
    "e8601da": "yyyy-MM-dd", "e8601dt": "yyyy-MM-dd'T'HH:mm:ss", "monyy7": "MMMyyyy", "year4": "yyyy",
    "mmyy": "MM/yyyy", "yymmn6": "yyyyMM", "ddmmyyn8": "ddMMyyyy",
}  # fmt: skip
_UNIT = {"day": "dd", "month": "MM", "year": "yyyy", "week": "dd", "hour": "HH", "minute": "mm", "second": "ss"}
_PART = {"year": "YEAR", "month": "MONTH", "day": "DAY_OF_MONTH", "weekday": "DAY_OF_WEEK"}
_CMP = {"=": "eq", "eq": "eq", "^=": "ne", "~=": "ne", "¬=": "ne", "ne": "ne", "<>": "ne", ">": "gt", "gt": "gt",
        "<": "lt", "lt": "lt", ">=": "ge", "ge": "ge", "<=": "le", "le": "le"}  # fmt: skip
_FORMAT_ARGS = {"input", "inputn", "inputc", "put", "putn", "putc"}

_TOKEN = re.compile(
    r"""\s*(?:
    (?P<datelit>'[0-9]{1,2}[A-Za-z]{3}[0-9]{2,4}'[dD])
    |(?P<name>(?:[A-Za-z_]\w*\.)?'[^']+'[nN])
    |(?P<str>'(?:[^']|'')*'|"(?:[^"]|"")*")
    |(?P<fmt>(?:\$?[A-Za-z_]+\d*\.\d*|\$\d+\.\d*)(?![\w]))
    |(?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)
    |(?P<mvar>&+[A-Za-z_]\w*\.?)
    |(?P<op>\*\*|\^=|~=|¬=|<>|>=|<=|\|\||!!|=|>|<|\+|-|\*|/|\(|\)|,|&|\||\^|~|¬|\.)
    |(?P<id>[A-Za-z_À-ɏ][\wÀ-ɏ]*(?:\.[A-Za-z_À-ɏ][\wÀ-ɏ]*)?)
    )""",
    re.VERBOSE,
)


class Unsupported(Exception):
    pass


@dataclass
class E:
    """Una expresión Java y su clase: num/str (literal), bool, null, date, any (columna o cálculo de tipo desconocido)."""

    java: str
    kind: str = "any"


class Result:
    def __init__(self, java: str, columns: list[str], warnings: list[str], kind: str = "any"):
        self.java, self.columns, self.warnings, self.kind = java, columns, warnings, kind


def _tokens(text: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise Unsupported(f"token no soportado: {text[pos : pos + 12]!r}")
        out.append((m.lastgroup or "", m.group(m.lastgroup or "")))
        pos = m.end()
    return out


def _jstr(raw: str) -> str:
    body = raw[1:-1].replace(raw[0] * 2, raw[0]).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{body}"'


def _num(e: E) -> str:
    """El valor numérico de una expresión; los literales van tal cual."""
    return e.java if e.kind == "num" else f"((Number) {e.java}).doubleValue()"


def _str(e: E) -> str:
    """La expresión como cadena, con el perdido de SAS (null) como cadena vacía."""
    return e.java if e.kind == "str" else f"({e.java} == null ? \"\" : {e.java})"


def _guard(parts: list[E], expr: str) -> str:
    """`expr` si ningún operando es perdido; si no, null (un perdido propaga)."""
    nulls = [p.java for p in parts if p.kind not in ("num", "str")]
    return f"({' || '.join(f'{n} == null' for n in nulls)} ? null : {expr})" if nulls else f"({expr})"


def _truth(e: E) -> str:
    if e.kind == "bool":
        return e.java
    if e.kind == "num":
        return f"({e.java} != 0)"
    return f"({e.java} != null && {_num(e)} != 0)"


def _compare(op: str, a: E, b: E) -> E:
    if op in ("eq", "ne"):
        if "null" in (a.kind, b.kind):
            core = f"Relational.ISNULL({b.java if a.kind == 'null' else a.java})"
        elif "str" in (a.kind, b.kind):
            lit, other = (a, b) if a.kind == "str" else (b, a)
            core = f"{lit.java}.equals({other.java})"
        elif "num" in (a.kind, b.kind):
            lit, other = (a, b) if a.kind == "num" else (b, a)
            core = f"({lit.java} == {other.java})" if other.kind == "num" else f"({other.java} != null && {_num(other)} == {lit.java})"
        else:
            core = f"java.util.Objects.equals({a.java}, {b.java})"
        return E(core if op == "eq" else f"(!{core})", "bool")
    num_lit_left, num_lit_right = a.kind == "num", b.kind == "num"
    if num_lit_left != num_lit_right:
        lit_left = num_lit_left
        other = b if lit_left else a
        # Con el literal a la izquierda se da la vuelta: 5 < x  ==  x > 5
        flip = {"lt": "gt", "gt": "lt", "le": "ge", "ge": "le"}
        eff = flip[op] if lit_left else op
        lit = a.java if lit_left else b.java
        sym = {"lt": "<", "le": "<=", "gt": ">", "ge": ">="}[eff]
        # En SAS un perdido numérico es menor que cualquier número.
        miss = "==" if eff in ("lt", "le") else "!="
        joiner = "||" if eff in ("lt", "le") else "&&"
        return E(f"({other.java} {miss} null {joiner} {_num(other)} {sym} {lit})", "bool")
    sym = {"lt": "< 0", "le": "<= 0", "gt": "> 0", "ge": ">= 0"}[op]
    cmpx = f"((Comparable) {a.java}).compareTo({b.java}) {sym}"
    if op == "lt":
        return E(f"({a.java} == null ? {b.java} != null : ({b.java} != null && {cmpx}))", "bool")
    if op == "le":
        return E(f"({a.java} == null || ({b.java} != null && {cmpx}))", "bool")
    if op == "gt":
        return E(f"({b.java} == null ? {a.java} != null : ({a.java} != null && {cmpx}))", "bool")
    return E(f"({b.java} == null || ({a.java} != null && {cmpx}))", "bool")


def _date_pattern(fmt: str) -> str | None:
    return DATE_FORMATS.get(fmt.lower().strip(".$'\"").rstrip("."))


class _P:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.t, self.i = tokens, 0
        self.cols: list[str] = []
        self.warnings: set[str] = set()

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
            if pattern.kind != "str":
                raise Unsupported("LIKE con un patrón que no es literal")
            regex = _jstr("'" + re.sub(r"%", ".*", re.sub(r"_", ".", pattern.java[1:-1])) + "'")
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
            return E(_guard([base, exponent], f"Double.valueOf(Math.pow({_num(base)}, {_num(exponent)}))"))
        return base

    def unary(self) -> E:
        if self.peek()[1] == "-":
            self.take()
            inner = self.unary()
            return E(f"-{inner.java}", "num") if inner.kind == "num" else E(_guard([inner], f"Double.valueOf(-{_num(inner)})"))
        if self.peek()[1] == "+":
            self.take()
            return self.unary()
        return self.atom()

    # ---- átomos
    def atom(self) -> E:
        k, v = self.take()
        if k == "str":
            return E(_jstr(v), "str")
        if k == "datelit":
            return E(f'TalendDate.parseDateLocale("ddMMMyyyy", "{v[1:-2]}", "en")', "date")
        if k == "num":
            return E(v if re.search(r"[.eE]", v) else v + ".0" if False else v, "num")
        if k == "fmt":
            return E(_jstr(f"'{v}'"), "str")
        if k == "mvar":
            name = v.lstrip("&").rstrip(".")
            self.warnings.add(f"Macrovariable &{name} -> context.sas_param_{name} (crear la variable de contexto)")
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
        return E(f"input_row.{name}")

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
                args.append(self.raw_format() if name in _FORMAT_ARGS and len(args) == 1 else self.expr())
                if self.peek()[1] != ",":
                    break
                self.take()
        self.expect(")")
        builder = _FUNCTIONS.get(name)
        if builder is None:
            raise Unsupported(f"función {name}")
        return builder(self, args)

    def raw_format(self) -> E:
        """El formato de `input`/`put` (`date9.`, `$10.`, `8.`) es un nombre, no una expresión."""
        parts, depth = [], 0
        while self.i < len(self.t):
            _kind, v = self.peek()
            if depth == 0 and v in (",", ")"):
                break
            depth += v == "("
            depth -= v == ")"
            parts.append(v.strip("'\""))
            self.i += 1
        return E(_jstr("'" + "".join(parts) + "'"), "str")


# ---------------------------------------------------------------------------------------------------------------------
# Funciones: cada una recibe los argumentos ya traducidos y devuelve una expresión. Solo rutinas de Talend y Java nativo.
# ---------------------------------------------------------------------------------------------------------------------


def _need(args: list[E], low: int, high: int | None = None, name: str = "") -> None:
    if not low <= len(args) <= (high if high is not None else low):
        raise Unsupported(f"{name}: número de argumentos no soportado ({len(args)})")


def _routine(routine: str, method: str, arity: int | None = None):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, arity or len(args), arity or len(args), method)
        return E(f"{routine}.{method}({', '.join(a.java for a in args)})")

    return build


def _strfn(template: str, arity: int = 1):
    """Función de texto que, ante un perdido (null), devuelve null."""

    def build(_p: _P, args: list[E]) -> E:
        _need(args, arity, arity, template)
        out = template.format(*[a.java for a in args])
        return E(_guard(args[:1], out) if args[0].kind != "str" else out, "str")

    return build


def _cat(trim: bool, sep: bool = False):
    def build(_p: _P, args: list[E]) -> E:
        if sep:
            if len(args) < 2:
                raise Unsupported("catx necesita separador y valores")
            glue, items = args[0], args[1:]
        else:
            glue, items = E('""', "str"), args
        parts = [f"StringHandling.TRIM({_str(i)})" if trim else _str(i) for i in items]
        if sep:  # catx omite los vacíos
            return E("String.join(" + glue.java + ", java.util.stream.Stream.of(" + ", ".join(parts)
                     + ").filter(s -> !s.isEmpty()).toArray(String[]::new))", "str")
        return E("(" + " + ".join(parts) + ")", "str")

    return build


def _substr(_p: _P, args: list[E]) -> E:
    _need(args, 2, 3, "substr")
    s, start = args[0], args[1]
    end = f", {_num(start)} - 1 + {_num(args[2])}" if len(args) == 3 else ""
    body = f"{s.java}.substring((int) {_num(start)} - 1{(', (int) (' + end[2:] + ')') if end else ''})"
    return E(_guard([s], body), "str")


def _scan(p: _P, args: list[E]) -> E:
    _need(args, 2, 3, "scan")
    if args[1].kind != "num" or (len(args) == 3 and args[2].kind != "str"):
        raise Unsupported("scan con posición o delimitadores que no son literales")
    delims = re.escape(args[2].java[1:-1]) if len(args) == 3 else r"\\s,;"
    n = int(float(args[1].java))
    p.warnings.add("scan: los delimitadores consecutivos cuentan como uno, como en SAS")
    tokens = f'{args[0].java}.replaceAll("^[{delims}]+", "").split("[{delims}]+")'
    return E(_guard([args[0]], f"({tokens}.length >= {n} ? {tokens}[{n - 1}] : null)"), "str")


def _compress(p: _P, args: list[E]) -> E:
    _need(args, 1, 2, "compress")
    chars = args[1].java[1:-1] if len(args) == 2 and args[1].kind == "str" else " "
    if len(args) == 2 and args[1].kind != "str":
        raise Unsupported("compress con caracteres que no son literales")
    if len(chars) == 1:
        return E(_guard([args[0]], f"StringHandling.CHANGE({args[0].java}, {_jstr(chr(39) + chars + chr(39))}, \"\")"), "str")
    return E(_guard([args[0]], f"StringHandling.EREPLACE({args[0].java}, \"[{re.escape(chars)}]\", \"\")"), "str")


def _round(_p: _P, args: list[E]) -> E:
    """ROUND de SAS redondea el 0,5 hacia fuera del cero (`Math.round` lo lleva hacia arriba: -2,5 -> -2)."""
    _need(args, 1, 2, "round")
    x = args[0]
    if len(args) == 1:
        v = _num(x)
        return E(_guard([x], f"Double.valueOf({v} < 0 ? -Math.round(-{v}) : Math.round({v}))"), "num")
    unit = args[1]
    v, u = _num(x), _num(unit)
    q = f"({v} / {u})"
    return E(
        _guard([x, unit], f"Double.valueOf(({q} < 0 ? -Math.round(-{q}) : Math.round({q})) * {u})"), "num"
    )


def _unary_math(fn: str):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, 1, 1, fn)
        return E(_guard(args, f"Double.valueOf({fn}({_num(args[0])}))"), "num")

    return build


def _int(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "int")
    return E(_guard(args, f"Long.valueOf(((Number) {args[0].java}).longValue())"), "num")


def _coalesce(_p: _P, args: list[E]) -> E:
    out = args[-1].java
    for a in reversed(args[:-1]):
        out = f"({a.java} != null ? {a.java} : {out})"
    return E(out)


def _ifv(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "ifn/ifc")
    return E(f"({_truth(args[0])} ? {args[1].java} : {args[2].java})")


def _aggregate(kind: str):
    def build(_p: _P, args: list[E]) -> E:
        if not args:
            raise Unsupported(f"{kind} sin argumentos")
        present = [a for a in args if a.kind != "null"]
        if kind in ("n", "nmiss"):
            test = "!=" if kind == "n" else "=="
            return E("(" + " + ".join(f"({a.java} {test} null ? 1 : 0)" for a in present) + ")")
        if kind == "sum":  # SUM ignora los perdidos
            return E("Double.valueOf(" + " + ".join(f"({a.java} == null ? 0 : {_num(a)})" for a in present) + ")")
        if kind == "mean":
            vals = " + ".join(f"({a.java} == null ? 0 : {_num(a)})" for a in present)
            count = " + ".join(f"({a.java} == null ? 0 : 1)" for a in present)
            return E(f"(({count}) == 0 ? null : Double.valueOf(({vals}) / ({count})))")
        fn = "Math.max" if kind == "max" else "Math.min"
        out = _num(present[-1])
        for a in reversed(present[:-1]):
            out = f"({a.java} == null ? {out} : {fn}({_num(a)}, {out}))"
        # Todos perdidos es perdido en SAS; sin esta guarda la anidacion desreferencia un null.
        empty = " && ".join(f"{a.java} == null" for a in present)
        return E(f"({empty} ? null : Double.valueOf({out}))")

    return build


def _input(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "input")
    fmt = args[1].java.strip("\"'").lower().rstrip(".")
    pattern = _date_pattern(fmt)
    if pattern:
        return E(f"TalendDate.parseDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "date")
    if fmt.startswith(("$", "char")):
        return E(args[0].java, "str")
    p.warnings.add("input numérico: el valor se convierte con Mathematical.REAL; comprobar el informato")
    return E(_guard(args[:1], f"Mathematical.REAL(StringHandling.TRIM({args[0].java}))"))


def _put(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "put")
    fmt = args[1].java.strip("\"'").lower().rstrip(".")
    pattern = _date_pattern(fmt)
    if pattern:
        return E(f"TalendDate.formatDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "str")
    zero = re.fullmatch(r"z(\d+)", fmt)
    if zero:
        return E(f'StringHandling.LPAD(String.valueOf({args[0].java}), {zero.group(1)}, "0")', "str")
    if re.fullmatch(r"\$?\d*", fmt) or fmt.startswith("$"):
        return E(f"String.valueOf({args[0].java})", "str")
    raise Unsupported(f"put con el formato {fmt}.")


def _intnx(_p: _P, args: list[E]) -> E:
    _need(args, 3, 4, "intnx")
    unit_arg, d, n = args[0], args[1], args[2]
    unit = unit_arg.java.strip('"').lower()
    if unit_arg.kind != "str" or unit not in _UNIT:
        raise Unsupported("intnx con un intervalo que no es literal o no está soportado")
    count = f"(int) ({_num(n)} * 7)" if unit == "week" else f"(int) {_num(n)}"
    moved = f'TalendDate.addDate({d.java}, {count}, "{_UNIT[unit]}")'
    align = args[3].java.strip('"').lower() if len(args) == 4 else "b"
    if unit == "month" and align == "e":
        moved = f"TalendDate.getLastDayOfMonth({moved})"
    elif unit == "month" and align == "b":
        moved = f"TalendDate.getFirstDayOfMonth({moved})"
    return E(_guard([d], moved), "date")


def _intck(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "intck")
    unit = args[0].java.strip('"').lower()
    if args[0].kind != "str" or unit not in _UNIT:
        raise Unsupported("intck con un intervalo que no es literal o no está soportado")
    return E(_guard(args[1:], f'Long.valueOf(TalendDate.diffDate({args[2].java}, {args[1].java}, "{_UNIT[unit]}"))'))


def _part(name: str):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, 1, 1, name)
        inc = " + 1" if name == "month" else ""
        return E(_guard(args, f'(TalendDate.getPartOfDate("{_PART[name]}", {args[0].java}){inc})'))

    return build


def _mdy(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "mdy")
    m, d, y = args
    text = f'String.format("%04d-%02d-%02d", (int) {_num(y)}, (int) {_num(m)}, (int) {_num(d)})'
    return E(_guard(args, f'TalendDate.parseDate("yyyy-MM-dd", {text})'), "date")


def _datepart(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "datepart")
    return E(_guard(args, f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-MM-dd", {args[0].java}))'), "date")


_FUNCTIONS = {
    "upcase": _routine("StringHandling", "UPCASE", 1), "lowcase": _routine("StringHandling", "DOWNCASE", 1),
    "strip": _routine("StringHandling", "TRIM", 1), "trim": _routine("StringHandling", "RTRIM", 1),
    "left": _routine("StringHandling", "LTRIM", 1), "tranwrd": _routine("StringHandling", "CHANGE", 3),
    "count": _routine("StringHandling", "COUNT", 2),
    "length": _strfn("StringHandling.LEN(StringHandling.RTRIM({0}))"), "lengthc": _strfn("StringHandling.LEN({0})"),
    "lengthn": _strfn("StringHandling.LEN(StringHandling.RTRIM({0}))"),
    "compbl": _strfn('StringHandling.EREPLACE({0}, " +", " ")'), "reverse": _strfn("new StringBuilder({0}).reverse().toString()"),
    "cat": _cat(False), "cats": _cat(True), "catt": _cat(True), "catx": _cat(True, sep=True),
    "substr": _substr, "substrn": _substr, "scan": _scan, "compress": _compress,
    "index": lambda p, a: E(f"({a[0].java}.indexOf({a[1].java}) + 1)") if len(a) == 2 else (_ for _ in ()).throw(Unsupported("index")),
    "abs": _unary_math("Math.abs"), "ceil": _unary_math("Math.ceil"), "floor": _unary_math("Math.floor"),
    "sqrt": _routine("Mathematical", "SQRT", 1), "exp": _routine("Mathematical", "EXP", 1),
    "log": _routine("Mathematical", "LN", 1), "mod": _routine("Mathematical", "MOD", 2),
    "round": _round, "int": _int,
    "coalesce": _coalesce, "coalescec": _coalesce, "ifn": _ifv, "ifc": _ifv,
    "missing": lambda p, a: E(f"Relational.ISNULL({a[0].java})", "bool"),
    "max": _aggregate("max"), "min": _aggregate("min"), "sum": _aggregate("sum"), "mean": _aggregate("mean"),
    "n": _aggregate("n"), "nmiss": _aggregate("nmiss"),
    "input": _input, "inputn": _input, "inputc": _input, "put": _put, "putn": _put, "putc": _put,
    "today": lambda p, a: E("TalendDate.getCurrentDate()", "date"), "date": lambda p, a: E("TalendDate.getCurrentDate()", "date"),
    "datetime": lambda p, a: E("TalendDate.getCurrentDate()", "date"),
    "datepart": _datepart, "mdy": _mdy, "intnx": _intnx, "intck": _intck,
    "year": _part("year"), "month": _part("month"), "day": _part("day"), "weekday": _part("weekday"),
}  # fmt: skip


def _clean(text: str) -> str:
    """Quita lo que acompaña a una expresión de PROC SQL y no es parte de ella."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?i)^(on|where|having)\s+", "", text)
    text = re.sub(r"(?i)^distinct\s+", "", text)
    text = re.sub(r"(?i)\s+(label|format|informat|length)\s*=\s*(\"[^\"]*\"|'[^']*'|\S+)\s*$", "", text)
    text = re.sub(r"(?i)\s+as\s+\w+\s*$", "", text)
    return text.strip()


def translate_to_talend(sas: str) -> Result:
    """Traduce una expresión SAS a Java con rutinas de Talend; `Unsupported` si no hay traducción segura."""
    text = _clean(sas)
    if not text:
        raise Unsupported("expresión vacía")
    parser = _P(_tokens(text))
    result = parser.expr()
    if parser.i != len(parser.t):
        raise Unsupported(f"texto sobrante: {parser.peek()[1]!r}")
    return Result(result.java, sorted(set(parser.cols)), sorted(parser.warnings), result.kind)
