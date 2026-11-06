"""Funciones SAS del traductor de Talend: cada una emite su rutina o su Java (usadas por `talend_tabla`)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import (
    _PART,
    _UNIT,
    E,
    Unsupported,
    _date_pattern,
    _guard,
    _jstr,
    _need,
    _num,
    _truth,
)
from sgm.expressions.talend_funciones_texto import _cat as _cat
from sgm.expressions.talend_funciones_texto import _compress as _compress
from sgm.expressions.talend_funciones_texto import _scan as _scan
from sgm.expressions.talend_funciones_texto import _strfn as _strfn
from sgm.expressions.talend_funciones_texto import _substr as _substr


def _routine(routine: str, method: str, arity: int | None = None):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, arity or len(args), arity or len(args), method)
        return E(f"{routine}.{method}({', '.join(a.java for a in args)})")

    return build


def _round(_p: _P, args: list[E]) -> E:
    """ROUND conserva el tipo numérico y redondea los empates alejándose de cero."""
    _need(args, 1, 2, "round")
    x = args[0]
    unit = args[1] if len(args) == 2 else E("1", "num")
    v, u = _num(x), _num(unit)
    q = v if len(args) == 1 else f"({v} / {u})"
    rounded = f"Math.copySign(Math.floor(Math.abs({q}) + 0.5), {q})"
    result = rounded if len(args) == 1 else f"({rounded} * {u})"
    return E(
        _guard([x, *([unit] if len(args) == 2 else [])], f"Double.valueOf({result})"),
        "num",
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
            return E(
                "Double.valueOf("
                + " + ".join(f"({a.java} == null ? 0 : {_num(a)})" for a in present)
                + ")"
            )
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
    if args[1].literal is None:
        raise Unsupported("informat dinámico o no literal; queda pendiente de resolución")
    fmt = args[1].literal.lower().rstrip(".")
    pattern = _date_pattern(fmt)
    if pattern:
        return E(
            f"TalendDate.parseDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "date"
        )
    if fmt.startswith(("$", "char")):
        return E(args[0].java, "str")
    width_decimal = re.fullmatch(r"\d+\.(\d+)", fmt)
    if width_decimal:
        decimals = int(width_decimal.group(1))
        source = f"StringHandling.TRIM({args[0].java})"
        pattern = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
        valid = f"{source}.matches({_jstr(chr(34) + pattern + chr(34))})"
        value = (
            f"new java.math.BigDecimal({source}).movePointLeft("
            f"{source}.contains({_jstr(chr(34) + chr(46) + chr(34))}) ? 0 : {decimals})"
        )
        return E(_guard([args[0]], f"({valid} ? {value} : null)"), "num")
    p.warnings.add(
        "input numérico: el valor se convierte con Mathematical.REAL; comprobar el informato"
    )
    return E(_guard(args[:1], f"Mathematical.REAL(StringHandling.TRIM({args[0].java}))"))


def _put(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "put")
    if args[1].literal is None:
        raise Unsupported("formato dinámico o no literal; queda pendiente de resolución")
    fmt = args[1].literal.lower().rstrip(".")
    pattern = _date_pattern(fmt)
    if pattern:
        return E(
            f"TalendDate.formatDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "str"
        )
    zero = re.fullmatch(r"z(\d+)", fmt)
    if zero:
        return E(
            f'StringHandling.LPAD(String.valueOf({args[0].java}), {zero.group(1)}, "0")', "str"
        )
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
    return E(
        _guard(
            args[1:],
            f'Long.valueOf(TalendDate.diffDate({args[2].java}, {args[1].java}, "{_UNIT[unit]}"))',
        )
    )


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
    return E(
        _guard(
            args,
            f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-MM-dd", {args[0].java}))',
        ),
        "date",
    )
