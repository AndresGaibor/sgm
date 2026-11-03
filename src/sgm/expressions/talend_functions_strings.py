"""Funciones de texto de SAS con rutinas de Talend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import ExpressionParser as _P

import re

from sgm.expressions.talend_core import E, Unsupported, _guard, _jstr, _need, _num, _str


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
    if not re.fullmatch(r"-?\d+", args[1].java):
        raise Unsupported("scan con una posición que no es entera")
    n = int(args[1].java)
    if n == 0 or abs(n) > 2_147_483_647:
        raise Unsupported("scan con una posición fuera del rango seguro")
    delims = re.escape(args[2].java[1:-1]) if len(args) == 3 else r"\\s,;"
    p.warnings.add("scan: los delimitadores consecutivos cuentan como uno, como en SAS")
    tokens = f'{args[0].java}.replaceAll("^[{delims}]+", "").split("[{delims}]+")'
    index = str(n - 1) if n > 0 else f"{tokens}.length + {n}"
    return E(
        _guard([args[0]], f"({tokens}.length >= {abs(n)} ? {tokens}[{index}] : null)"), "str"
    )


def _compress(p: _P, args: list[E]) -> E:
    _need(args, 1, 3, "compress")
    if len(args) == 3:
        if args[2].java != '"kd"':
            raise Unsupported("compress con modificadores no demostrados")
        if args[1].kind == "omitted":
            pattern = "[^0-9]"
        elif args[1].kind == "str" and args[1].java == '"."':
            pattern = "[^0-9.]"
        else:
            raise Unsupported("compress con una lista de caracteres no demostrada")
        source = args[0]
        return E(
            _guard([source], f'StringHandling.EREPLACE({source.java}, "{pattern}", "")'), "str"
        )
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
