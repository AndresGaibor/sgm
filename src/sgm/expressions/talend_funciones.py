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
from sgm.expressions.talend_lexer import _collapse_whitespace_outside_strings


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
    if args[1].kind != "num" or not re.fullmatch(r"-?\d+", args[1].java):
        raise Unsupported("scan con una posición que no es entera")
    n = int(args[1].java)
    if n == 0 or abs(n) > 2_147_483_647:
        raise Unsupported(
            "scan con una posición no válida: debe ser distinta de cero y estar en el rango seguro"
        )
    explicito = len(args) == 3
    if explicito:
        if args[2].kind != "str" or not args[2].literal:
            raise Unsupported("scan con delimitadores vacíos o que no son literales")
        if any(not char.isprintable() for char in args[2].literal):
            raise Unsupported("scan con delimitadores de control: queda pendiente de revisión")
        delims = re.escape(args[2].literal)
        prefijo = _jstr(chr(39) + f"^[{delims}]+" + chr(39))
        separador = _jstr(chr(39) + f"[{delims}]+" + chr(39))
    else:
        # Ya viene escrito para Java: se incrusta tal cual, sin volver a escapar la barra.
        delims = r"\\s!$%&()*+,\\-./;\\x3c^"
        prefijo = f'"^[{delims}]+"'
        separador = f'"[{delims}]+"'
    p.warnings.add("scan: los delimitadores consecutivos cuentan como uno, como en SAS")
    tokens = f'{args[0].java}.replaceAll({prefijo}, "").split({separador})'
    # Con delimitadores declarados o cuenta negativa se indexa el arreglo; el `skip` no sabe contar
    # desde el final, y sin delimitadores el flujo perezoso es el que ya se emitía.
    if explicito or n < 0:
        index = str(n - 1) if n > 0 else f"{tokens}.length + {n}"
        return E(
            _guard([args[0]], f"({tokens}.length >= {abs(n)} ? {tokens}[{index}] : null)"), "str"
        )
    body = f'java.util.Arrays.stream({tokens}).skip({n - 1}).findFirst().orElse("")'
    return E(_guard([args[0]], body), "str")


def _compress(p: _P, args: list[E]) -> E:
    _need(args, 1, 3, "compress")
    if len(args) == 1:
        return E(
            _guard(
                [args[0]],
                f'StringHandling.CHANGE({args[0].java}, {_jstr(chr(39) + " " + chr(39))}, "")',
            ),
            "str",
        )
    if args[1].kind == "omitted":
        # Solo `kd` está demostrado con la lista omitida (quitar todo lo que no sea dígito).
        if len(args) == 3 and (args[2].kind != "str" or args[2].literal.lower() != "kd"):
            raise Unsupported("compress con la lista omitida y modificadores no demostrados")
        chars = ""
    elif args[1].kind != "str" or args[1].literal is None:
        raise Unsupported("compress con caracteres o modificadores no literales")
    else:
        chars = args[1].literal
    if not chars and len(args) == 2:
        raise Unsupported("compress con una lista de caracteres vacía")
    if any(not char.isprintable() for char in chars):
        raise Unsupported("compress con caracteres de control: queda pendiente de revisión")
    modifiers = ""
    if len(args) == 3:
        if args[2].kind != "str" or args[2].literal is None:
            raise Unsupported("compress con caracteres o modificadores no literales")
        modifiers = args[2].literal.lower()
    # `kd` solo está demostrado para quitar todo lo que no sea dígito, con o sin punto decimal.
    if modifiers == "kd":
        if chars == "":
            patron = "[^0-9]"
        elif chars == ".":
            patron = "[^0-9.]"
        else:
            raise Unsupported("compress con 'kd' y una lista de caracteres no demostrada")
        return E(
            _guard(
                [args[0]],
                f'StringHandling.EREPLACE({args[0].java}, {_jstr(chr(34) + patron + chr(34))}, "")',
            ),
            "str",
        )
    if len(args) == 2:
        if len(chars) == 1:
            return E(
                _guard(
                    [args[0]],
                    f'StringHandling.CHANGE({args[0].java}, {_jstr(chr(39) + chars + chr(39))}, "")',
                ),
                "str",
            )
        return E(
            _guard(
                [args[0]],
                f'StringHandling.EREPLACE({args[0].java}, {_jstr(chr(34) + "[" + re.escape(chars) + "]" + chr(34))}, "")',
            ),
            "str",
        )
    desconocidos = set(modifiers) - {"d", "i", "k"}
    if desconocidos:
        raise Unsupported(
            "compress con modificadores no cubiertos: " + "".join(sorted(desconocidos))
        )

    alternativas = [r"\Q" + caracter.replace(r"\E", r"\E\\E\Q") + r"\E" for caracter in chars]
    if "d" in modifiers:
        alternativas.append("[0-9]")
    if not alternativas:
        kept = '""' if "k" in modifiers else args[0].java
        return E(_guard([args[0]], kept), "str")
    patron = "(?:" + "|".join(alternativas) + ")"
    if "i" in modifiers:
        patron = "(?i:" + patron + ")"
    if "k" in modifiers:
        patron = f"(?!(?:{patron}))[\\s\\S]"
    java = f"{args[0].java}.replaceAll({_jstr(chr(34) + patron + chr(34))}, \"\")"
    return E(_guard([args[0]], java), "str")


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
        raise Unsupported("input con un informat que no es literal")
    literal = args[1].literal.strip().strip("'\"")
    fmt = literal.lower()
    pattern = _date_pattern(fmt)
    if pattern:
        return E(
            f"TalendDate.parseDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "date"
        )
    if fmt.rstrip(".").startswith(("$", "char")):
        return E(args[0].java, "str")
    if re.fullmatch(r"\d+", fmt):
        raise Unsupported("input con un informat entero sin punto decimal: queda pendiente")
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
    literal = args[1].literal if args[1].literal is not None else args[1].java.strip("\"'")
    fmt = literal.lower()
    pattern = _date_pattern(fmt)
    if pattern:
        return E(
            f"TalendDate.formatDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "str"
        )
    zero = re.fullmatch(r"z(\d+)\.?", fmt)
    if zero:
        return E(
            f'StringHandling.LPAD(String.valueOf({args[0].java}), {zero.group(1)}, "0")', "str"
        )
    if re.fullmatch(r"\$?\d*\.?", fmt) or fmt.startswith("$"):
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
    """Quita lo que acompaña a una expresión de PROC SQL y no es parte de ella.

    Los espacios y los saltos de línea dentro de un literal son parte del valor SAS: no se colapsan.
    """
    text = _collapse_whitespace_outside_strings(text)
    text = re.sub(r"(?i)^(on|where|having)\s+", "", text)
    text = re.sub(r"(?i)^distinct\s+", "", text)
    text = re.sub(
        r"(?i)\s+(label|format|informat|length)\s*=\s*(\"[^\"]*\"|'[^']*'|\S+)\s*$", "", text
    )
    text = re.sub(r"(?i)\s+as\s+\w+\s*$", "", text)
    return text.strip()
