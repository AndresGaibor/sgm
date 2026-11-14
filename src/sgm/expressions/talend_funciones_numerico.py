"""Constructores Talend para funciones SAS numéricas y agregaciones por fila."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import E, Unsupported, _guard, _need, _num, _truth


def _finite(expression: str) -> str:
    """Convierte NaN e infinitos a missing sin repetir la expresión de entrada."""
    return (
        "((Double) ((java.util.function.DoubleFunction) "
        "(value -> Double.isFinite(value) ? value : null)).apply(" + expression + "))"
    )


def _round(_p: _P, args: list[E]) -> E:
    """ROUND conserva el tipo numérico y redondea los empates alejándose de cero."""
    _need(args, 1, 2, "round")
    x = args[0]
    unit = args[1] if len(args) == 2 else E("1", "num")
    v, u = _num(x), _num(unit)
    rounded = (
        "((java.util.function.DoubleBinaryOperator) ((value, unitValue) -> unitValue == 0 "
        "? Double.NaN : java.math.BigDecimal.valueOf(value)"
        ".divide(java.math.BigDecimal.valueOf(unitValue), 0, java.math.RoundingMode.HALF_UP)"
        ".multiply(java.math.BigDecimal.valueOf(unitValue)).doubleValue()))"
        f".applyAsDouble({v}, {u})"
    )
    result = _finite(rounded)
    return E(
        _guard([x, *([unit] if len(args) == 2 else [])], result),
        "num",
    )


def _unary_math(fn: str):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, 1, 1, fn)
        calculo = f"{fn}({_num(args[0])})"
        return E(_guard(args, _finite(calculo)), "num")

    return build


def _ceil_floor(fn: str):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, 1, 1, fn)
        desplazamiento = "- 1.0E-12" if fn == "Math.ceil" else "+ 1.0E-12"
        calculo = f"Double.valueOf({fn}({_num(args[0])} {desplazamiento}))"
        return E(_guard(args, calculo), "num")

    return build


def _mod(_p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "mod")
    a, b = (_num(arg) for arg in args)
    resto = f"({a} % {b})"
    return E(_guard(args, _finite(resto)), "num")


def _int(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "int")
    cuerpo = "Math.copySign(Math.floor(Math.abs(value) + 1.0E-12), value)"
    calculo = (
        "((Double) ((java.util.function.DoubleFunction) "
        f"(value -> {cuerpo})).apply({_num(args[0])}))"
    )
    return E(_guard(args, _finite(calculo)), "num")


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
