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
    _num,
    _str,
    _truth,
)


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
            return E(
                "String.join("
                + glue.java
                + ", java.util.stream.Stream.of("
                + ", ".join(parts)
                + ").filter(s -> !s.isEmpty()).toArray(String[]::new))",
                "str",
            )
        return E("(" + " + ".join(parts) + ")", "str")

    return build


def _substr(_p: _P, args: list[E]) -> E:
    _need(args, 2, 3, "substr")
    s, start = args[0], args[1]
    end = f", {_num(start)} - 1 + {_num(args[2])}" if len(args) == 3 else ""
    body = (
        f"{s.java}.substring((int) {_num(start)} - 1{(', (int) (' + end[2:] + ')') if end else ''})"
    )
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
        return E(
            _guard(
                [args[0]],
                f'StringHandling.CHANGE({args[0].java}, {_jstr(chr(39) + chars + chr(39))}, "")',
            ),
            "str",
        )
    return E(
        _guard([args[0]], f'StringHandling.EREPLACE({args[0].java}, "[{re.escape(chars)}]", "")'),
        "str",
    )


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


def _input(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "input")
    fmt = args[1].java.strip("\"'").lower().rstrip(".")
    pattern = _date_pattern(fmt)
    if pattern:
        return E(
            f"TalendDate.parseDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "date"
        )
    if fmt.startswith(("$", "char")):
        return E(args[0].java, "str")
    p.warnings.add(
        "input numérico: el valor se convierte con Mathematical.REAL; comprobar el informato"
    )
    return E(_guard(args[:1], f"Mathematical.REAL(StringHandling.TRIM({args[0].java}))"))


def _put(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "put")
    fmt = args[1].java.strip("\"'").lower().rstrip(".")
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




def _clean(text: str) -> str:
    """Quita lo que acompaña a una expresión de PROC SQL y no es parte de ella."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?i)^(on|where|having)\s+", "", text)
    text = re.sub(r"(?i)^distinct\s+", "", text)
    text = re.sub(
        r"(?i)\s+(label|format|informat|length)\s*=\s*(\"[^\"]*\"|'[^']*'|\S+)\s*$", "", text
    )
    text = re.sub(r"(?i)\s+as\s+\w+\s*$", "", text)
    return text.strip()
