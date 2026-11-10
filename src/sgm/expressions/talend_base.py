"""Base del traductor de Talend: resultado, tokens, guardas de nulo y comparaciones (sin parser)."""

import re
from dataclasses import dataclass

from sgm.java_literals import literal_java

#: Informatos y formatos de fecha de SAS → patrón de Java para `TalendDate`.
DATE_FORMATS = {
    "yymmdd10": "yyyy-MM-dd", "yymmdd8": "yy-MM-dd", "yymmddn8": "yyyyMMdd", "ddmmyy10": "dd/MM/yyyy",
    "ddmmyy8": "dd/MM/yy", "mmddyy10": "MM/dd/yyyy", "mmddyy8": "MM/dd/yy", "date9": "ddMMMyyyy",
    "date7": "ddMMMyy", "datetime20": "ddMMMyyyy:HH:mm:ss", "datetime19": "ddMMMyyyy:HH:mm:ss",
    "e8601da": "yyyy-MM-dd", "e8601dt": "yyyy-MM-dd'T'HH:mm:ss", "monyy7": "MMMyyyy", "year4": "yyyy",
    "mmyy": "MM/yyyy", "yymmn6": "yyyyMM", "ddmmyyn8": "ddMMyyyy",
}  # fmt: skip
_UNIT = {
    "day": "dd",
    "month": "MM",
    "year": "yyyy",
    "week": "dd",
    "hour": "HH",
    "minute": "mm",
    "second": "ss",
}
_PART = {"year": "YEAR", "month": "MONTH", "day": "DAY_OF_MONTH", "weekday": "DAY_OF_WEEK"}
_CMP = {"=": "eq", "eq": "eq", "^=": "ne", "~=": "ne", "¬=": "ne", "ne": "ne", "<>": "ne", ">": "gt", "gt": "gt",
        "<": "lt", "lt": "lt", ">=": "ge", "ge": "ge", "<=": "le", "le": "le"}  # fmt: skip
_FORMAT_ARGS = {"input", "inputn", "inputc", "put", "putn", "putc"}

_TOKEN = re.compile(
    r"""\s*(?:
    (?P<datelit>'[0-9]{1,2}[A-Za-z]{3}[0-9]{2,4}'[dD])
    |(?P<name>(?:[A-Za-z_]\w*\.)?'[^']+'[nN])
    |(?P<str>'(?:[^']|'')*'|"(?:[^"]|"")*")
    |(?P<fmt>(?:\$?[A-Za-z_][A-Za-z_0-9]*\.\d*|\$\d+\.\d*)(?![\w]))
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
    literal: str | None = None


class Result:
    """Java candidato y metadatos extraídos al analizar la expresión SAS."""

    def __init__(
        self,
        java: str,
        columns: list[str],
        warnings: list[str],
        kind: str = "any",
        functions: list[str] | None = None,
    ):
        self.java, self.columns, self.warnings, self.kind = java, columns, warnings, kind
        self.functions = functions or []


def _tokens(text: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise Unsupported("token no soportado en la expresión; queda pendiente de revisión")
        out.append((m.lastgroup or "", m.group(m.lastgroup or "")))
        pos = m.end()
    return out


def _jstr(raw: str) -> str:
    if len(raw) < 2 or raw[-1] != raw[0]:
        return literal_java(raw)
    body = raw[1:-1].replace(raw[0] * 2, raw[0])
    return literal_java(body)


def _num(e: E) -> str:
    """El valor numérico de una expresión; los literales van tal cual."""
    return e.java if e.kind == "num" else f"((Number) {e.java}).doubleValue()"


def _str(e: E) -> str:
    """La expresión como cadena, con el perdido de SAS (null) como cadena vacía."""
    return e.java if e.kind == "str" else f'({e.java} == null ? "" : {e.java})'


def _guard(parts: list[E], expr: str) -> str:
    """`expr` si ningún operando es perdido; si no, null (un perdido propaga)."""
    nulls = [p.java for p in parts if p.kind not in ("num", "str")]
    return (
        f"({' || '.join(f'{n} == null' for n in nulls)} ? null : {expr})" if nulls else f"({expr})"
    )


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
            core = (
                f"({lit.java} == {other.java})"
                if other.kind == "num"
                else f"({other.java} != null && {_num(other)} == {lit.java})"
            )
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


def _need(args: list[E], low: int, high: int | None = None, name: str = "") -> None:
    if not low <= len(args) <= (high if high is not None else low):
        raise Unsupported(f"{name}: número de argumentos no soportado ({len(args)})")
