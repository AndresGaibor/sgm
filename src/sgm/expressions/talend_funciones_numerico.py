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
    if not args:
        raise Unsupported("COALESCE requiere argumentos")
    if any(arg.kind == "str" for arg in args):
        return _coalesce_texto(args, "COALESCE")
    if any(a.kind in ("str", "date", "bool") for a in args):
        raise Unsupported("COALESCE requiere argumentos numéricos")
    if not any(arg.kind in ("num", "null") for arg in args):
        raise Unsupported("tipo de COALESCE sin demostrar: queda pendiente")
    values = "java.util.Arrays.asList(" + ", ".join(arg.java for arg in args) + ")"
    expression = (
        values
        + ".stream().filter(value -> value != null)"
        ".map(value -> ((Number) value).doubleValue()).findFirst().orElse(null)"
    )
    return E(expression, "num")


def _coalesce_texto(args: list[E], nombre: str) -> E:
    if any(arg.kind in ("num", "date", "bool") for arg in args):
        raise Unsupported(f"{nombre} requiere argumentos de texto")
    values = "java.util.Arrays.asList(" + ", ".join(arg.java for arg in args) + ")"
    expression = (
        values
        + ".stream().filter(value -> value instanceof String "
        '&& !((String) value).replace(" ", "").isEmpty())'
        ".map(value -> (String) value).findFirst().orElse(\"\")"
    )
    return E(expression, "str")


def _coalescec(_p: _P, args: list[E]) -> E:
    if not args:
        raise Unsupported("COALESCEC requiere argumentos")
    return _coalesce_texto(args, "COALESCEC")


def _ifv(_p: _P, args: list[E], result_kind: str | None = None) -> E:
    _need(args, 3, 4, "ifn/ifc")
    condition, *branches = args
    if condition.kind in ("str", "date"):
        raise Unsupported("IFN/IFC requiere condición numérica")
    known_kinds = {branch.kind for branch in branches if branch.kind not in ("any", "null")}
    if len(known_kinds) > 1:
        raise Unsupported("IFN/IFC no admite ramas de tipos mezclados")
    inferred_kind = result_kind or next(iter(known_kinds), "any")
    if known_kinds and inferred_kind not in known_kinds:
        raise Unsupported(f"IFN/IFC requiere ramas {inferred_kind}")
    core = f"({_truth(condition)} ? {branches[0].java} : {branches[1].java})"
    if len(branches) == 3:
        if condition.kind == "null":
            core = branches[2].java
        elif condition.kind == "any":
            core = f"({condition.java} == null ? {branches[2].java} : {core})"
        elif condition.kind == "num" and condition.literal is None:
            faltante = f"java.util.Collections.singletonList({condition.java}).get(0) == null"
            core = f"({faltante} ? {branches[2].java} : {core})"
    return E(core, inferred_kind)


def _ifn(_p: _P, args: list[E]) -> E:
    return _ifv(_p, args, "num")


def _ifc(_p: _P, args: list[E]) -> E:
    return _ifv(_p, args, "str")


def _missing_test(arg: E) -> str:
    if arg.kind == "null":
        return "true"
    if arg.kind == "num":
        if arg.literal is not None:
            return "false"
        return f"(java.util.Collections.singletonList({arg.java}).get(0) == null)"
    if arg.kind == "str":
        return f'({arg.java} == null || {arg.java}.replace(" ", "").isEmpty())'
    if arg.kind == "date":
        return f"({arg.java} == null)"
    return (
        "((Boolean) ((java.util.function.Function) (value -> value == null || "
        '(value instanceof String && ((String) value).replace(" ", "").isEmpty())))'
        f".apply({arg.java}))"
    )


def _missing(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "missing")
    return E(_missing_test(args[0]), "bool")


def _aggregate(kind: str):
    def build(_p: _P, args: list[E]) -> E:
        if not args:
            raise Unsupported(f"{kind} sin argumentos")
        if kind == "cmiss":
            return E(
                "(" + " + ".join(f"({_missing_test(arg)} ? 1 : 0)" for arg in args) + ")",
                "num",
            )
        if kind in ("n", "nmiss"):
            if any(arg.kind in ("str", "date", "bool") for arg in args):
                raise Unsupported(f"{kind.upper()} requiere argumentos numéricos")
            conteos = []
            for arg in args:
                if arg.kind == "null":
                    conteos.append("1" if kind == "nmiss" else "0")
                elif arg.kind == "num":
                    conteos.append("0" if kind == "nmiss" else "1")
                else:
                    comparador = "==" if kind == "nmiss" else "!="
                    conteos.append(f"({arg.java} {comparador} null ? 1 : 0)")
            return E("(" + " + ".join(conteos) + ")", "num")

        if any(arg.kind in ("str", "date", "bool") for arg in args):
            raise Unsupported(f"{kind.upper()} requiere argumentos numéricos")
        present = [arg for arg in args if arg.kind != "null"]
        if not present:
            return E("null", "num")
        values = "java.util.Arrays.asList(" + ", ".join(arg.java for arg in present) + ")"
        stream = f"{values}.stream().filter(value -> value != null)"
        numeric_stream = stream + ".mapToDouble(value -> ((Number) value).doubleValue())"
        if kind == "sum":
            result = (
                numeric_stream
                + ".reduce(Double.NaN, (total, value) -> Double.isNaN(total) ? value : total + value)"
            )
        elif kind == "mean":
            result = numeric_stream + ".average().orElse(Double.NaN)"
        else:
            operation = "max" if kind == "max" else "min"
            result = numeric_stream + f".{operation}().orElse(Double.NaN)"
        return E(_finite(result), "num")

    return build
