"""Funciones numéricas y condicionales de SAS para Talend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import ExpressionParser as _P

from sgm.expressions.talend_core import E, Unsupported, _guard, _need, _num, _truth


def _round(_p: _P, args: list[E]) -> E:
    """ROUND de SAS redondea el 0,5 hacia fuera del cero (`Math.round` lo lleva hacia arriba: -2,5 -> -2)."""
    _need(args, 1, 2, "round")
    x = args[0]
    if len(args) == 1:
        v = _num(x)
        return E(
            _guard([x], f"Double.valueOf({v} < 0 ? -Math.round(-{v}) : Math.round({v}))"), "num"
        )
    unit = args[1]
    v, u = _num(x), _num(unit)
    q = f"({v} / {u})"
    return E(
        _guard([x, unit], f"Double.valueOf(({q} < 0 ? -Math.round(-{q}) : Math.round({q})) * {u})"),
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
