"""Constructores Talend para funciones SAS de texto."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import E, Unsupported, _guard, _jstr, _need, _num, _str


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
        if sep:
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
    source, start = args[0], args[1]
    end = f", {_num(start)} - 1 + {_num(args[2])}" if len(args) == 3 else ""
    body = (
        f"{source.java}.substring((int) {_num(start)} - 1"
        f"{(', (int) (' + end[2:] + ')') if end else ''})"
    )
    return E(_guard([source], body), "str")


def _scan(p: _P, args: list[E]) -> E:
    _need(args, 2, 3, "scan")
    if args[1].kind != "num" or (len(args) == 3 and args[2].kind != "str"):
        raise Unsupported("scan con posición o delimitadores que no son literales")
    if not re.fullmatch(r"-?\d+", args[1].java):
        raise Unsupported("scan con una posición que no es entera")
    n = int(args[1].java)
    if n == 0:
        raise Unsupported("scan requiere una posición distinta de cero")
    if abs(n) > 2_147_483_647:
        raise Unsupported("scan con una posición fuera del rango seguro")
    if len(args) == 3:
        delims = args[2].literal
        if delims is None or not delims or any(not char.isprintable() for char in delims):
            raise Unsupported("scan con delimitadores vacíos o que requieren escape no demostrado")
        delims = re.escape(delims)
    else:
        delims = r"\s!$%&()*+,\-./;\x3c^"
    p.warnings.add("scan: los delimitadores consecutivos cuentan como uno, como en SAS")
    prefix = _jstr('"^[' + delims + ']+"')
    token_pattern = _jstr('"[' + delims + ']+"')
    tokens = f"{args[0].java}.replaceAll({prefix}, \"\").split({token_pattern})"
    if n > 0:
        body = f"java.util.Arrays.stream({tokens}).skip({n - 1}).findFirst().orElse(\"\")"
    else:
        skip = f"Math.abs({tokens}.length - {abs(n)})"
        body = f"java.util.Arrays.stream({tokens}).skip({skip}).findFirst().orElse(\"\")"
    return E(_guard([args[0]], body), "str")


def _compress(p: _P, args: list[E]) -> E:
    _need(args, 1, 3, "compress")
    source = args[0]
    if len(args) == 1:
        return E(
            _guard([source], f'StringHandling.CHANGE({source.java}, " ", "")'), "str"
        )
    char_arg = args[1]
    if char_arg.kind not in ("str", "omitted") or (
        char_arg.kind == "str" and char_arg.literal is None
    ):
        raise Unsupported("compress con caracteres o modificadores no literales")
    chars = char_arg.literal if char_arg.kind == "str" else None
    if len(args) == 2:
        if chars is None or not chars or any(not char.isprintable() for char in chars):
            raise Unsupported("compress con una lista de caracteres vacía o no demostrada")
        regex = "[" + re.escape(chars) + "]"
        java_pattern = _jstr('"' + regex + '"')
        return E(
            _guard([source], f"StringHandling.EREPLACE({source.java}, {java_pattern}, \"\")"),
            "str",
        )

    modifier_arg = args[2]
    if modifier_arg.kind != "str" or modifier_arg.literal is None:
        raise Unsupported("compress con modificadores que no son literales")
    modifiers = modifier_arg.literal.lower()
    if any(not char.isprintable() for char in (chars or "") + modifier_arg.literal):
        raise Unsupported("compress con caracteres de control")

    if modifiers == "kd":
        if char_arg.kind == "omitted":
            regex = "[^0-9]"
        elif chars == ".":
            regex = "[^0-9.]"
        else:
            raise Unsupported("compress con modificadores no demostrados")
        java_pattern = _jstr('"' + regex + '"')
        return E(
            _guard([source], f"StringHandling.EREPLACE({source.java}, {java_pattern}, \"\")"),
            "str",
        )

    if modifiers == "d":
        if chars != "":
            raise Unsupported("compress con modificadores no demostrados")
        regex = "[0-9]"
        java_pattern = _jstr('"' + regex + '"')
        return E(
            _guard([source], f"StringHandling.EREPLACE({source.java}, {java_pattern}, \"\")"),
            "str",
        )

    if modifiers not in ("i", "k") or chars is None:
        raise Unsupported("compress con modificadores no demostrados")
    if not chars:
        if modifiers == "k":
            return E(_guard([source], '""'), "str")
        raise Unsupported("compress con una lista de caracteres vacía")

    alternatives = [r"\Q" + char.replace(r"\E", r"\E\\E\Q") + r"\E" for char in chars]
    pattern = "(?:" + "|".join(alternatives) + ")"
    if modifiers == "i":
        pattern = "(?i:" + pattern + ")"
    else:
        pattern = f"(?!(?:{pattern}))[\\s\\S]"
    java_pattern = _jstr('"' + pattern + '"')
    return E(
        _guard([source], f"{source.java}.replaceAll({java_pattern}, \"\")"), "str"
    )
