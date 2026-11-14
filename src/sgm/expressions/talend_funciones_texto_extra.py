"""Constructores Talend para funciones SAS de texto con reglas específicas."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

import re

from sgm.expressions.talend_base import E, Unsupported, _guard, _jstr, _need, _str


def _length(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "length")
    if args[0].kind == "null":
        return E("1", "num")
    texto = args[0].java if args[0].kind in ("str", "any") else _str(args[0])
    java = f"Math.max(StringHandling.LEN(StringHandling.RTRIM({texto})), 1)"
    if args[0].kind not in ("num", "str"):
        java = f"({args[0].java} == null ? 1 : {java})"
    return E(java, "num")


def _lengthn(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "lengthn")
    if args[0].kind == "null":
        return E("0", "num")
    texto = args[0].java if args[0].kind in ("str", "any") else _str(args[0])
    largo = f"StringHandling.RTRIM({texto})"
    java = f"{largo}.codePointCount(0, {largo}.length())"
    if args[0].kind not in ("num", "str"):
        java = f"({args[0].java} == null ? 0 : {java})"
    return E(java, "num")


def _lengthc(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "lengthc")
    if args[0].kind == "null":
        return E("0", "num")
    texto = args[0].java if args[0].kind in ("str", "any") else _str(args[0])
    java = f"{texto}.codePointCount(0, {texto}.length())"
    if args[0].kind not in ("num", "str"):
        java = f"({args[0].java} == null ? null : {java})"
    return E(java, "num")


def _count(_p: _P, args: list[E]) -> E:
    _need(args, 2, 3, "count")
    if len(args) == 2 or args[2].kind == "omitted":
        body = f"StringHandling.COUNT({args[0].java}, {args[1].java})"
        return E(_guard(args[:2], body), "num")
    modifier = args[2]
    if modifier.kind != "str" or modifier.literal is None:
        raise Unsupported("Pendiente: P-JAVA-COUNT-MODIFICADOR-DINAMICO")
    mods = modifier.literal.lower()
    if set(mods) - {"i", "t"}:
        raise Unsupported("Pendiente: P-JAVA-COUNT-MODIFICADOR")
    texto = args[0].java if args[0].kind in ("str", "any") else _str(args[0])
    buscar = args[1].java if args[1].kind in ("str", "any") else _str(args[1])
    if "t" in mods:
        texto, buscar = f"StringHandling.RTRIM({texto})", f"StringHandling.RTRIM({buscar})"
    if "i" in mods:
        texto = f"{texto}.toLowerCase(java.util.Locale.ROOT)"
        buscar = f"{buscar}.toLowerCase(java.util.Locale.ROOT)"
    body = f"StringHandling.COUNT({texto}, {buscar})"
    return E(_guard(args[:2], body), "num")


def _index(_p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "index")
    body = f"({args[0].java}.indexOf({args[1].java}) + 1)"
    return E(_guard(args, body), "num")


def _find(_p: _P, args: list[E]) -> E:
    _need(args, 2, 4, "find")
    mods = ""
    start_arg = None
    modifier = None
    if len(args) >= 3 and args[2].kind != "omitted":
        if args[2].kind == "str":
            modifier = args[2]
            start_arg = args[3] if len(args) == 4 else None
        elif args[2].kind == "num":
            start_arg = args[2]
            modifier = args[3] if len(args) == 4 else None
        else:
            raise Unsupported("Pendiente: P-JAVA-FIND-INICIO-O-MODIFICADOR-DINAMICO")
    elif len(args) == 4:
        if args[3].kind == "num":
            start_arg = args[3]
        elif args[3].kind == "str":
            modifier = args[3]
    if modifier is not None:
        if modifier.kind != "str" or modifier.literal is None:
            raise Unsupported("Pendiente: P-JAVA-FIND-MODIFICADOR-DINAMICO")
        mods = modifier.literal.lower()
    if set(mods) - {"i", "t"}:
        raise Unsupported("Pendiente: P-JAVA-FIND-MODIFICADOR")
    start = 1
    if start_arg is not None and start_arg.kind != "omitted":
        if start_arg.kind != "num" or not re.fullmatch(r"-?\d+(?:\.0+)?", start_arg.java):
            raise Unsupported("Pendiente: P-JAVA-FIND-INICIO-DINAMICO")
        start = int(float(start_arg.java))
        if abs(start) > 2_147_483_647:
            raise Unsupported("Pendiente: P-JAVA-FIND-INICIO-FUERA-DE-RANGO")
    if start == 0:
        return E("0", "num")
    texto = args[0].java if args[0].kind in ("str", "any") else _str(args[0])
    buscar = args[1].java if args[1].kind in ("str", "any") else _str(args[1])
    if "t" in mods:
        texto, buscar = f"StringHandling.RTRIM({texto})", f"StringHandling.RTRIM({buscar})"
    if "i" in mods:
        texto = f"{texto}.toLowerCase(java.util.Locale.ROOT)"
        buscar = f"{buscar}.toLowerCase(java.util.Locale.ROOT)"
    if start < 0:
        body = f"{texto}.lastIndexOf({buscar}, {abs(start) - 1}) + 1"
    else:
        body = f"{texto}.indexOf({buscar}, {start - 1}) + 1"
    return E(_guard(args[:2], body), "num")


def _translate(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "translate")
    destino, origen = args[1], args[2]
    if any(arg.kind != "str" or arg.literal is None for arg in (destino, origen)):
        raise Unsupported("Pendiente: P-JAVA-TRANSLATE-LISTA-DINAMICA")
    if not all(caracter.isascii() for caracter in destino.literal + origen.literal):
        raise Unsupported("Pendiente: P-JAVA-TRANSLATE-CODIFICACION-SBCS")
    if len(set(origen.literal)) != len(origen.literal):
        raise Unsupported("Pendiente: P-JAVA-TRANSLATE-ORIGEN-DUPLICADO")
    pares = list(zip(origen.literal, destino.literal, strict=False))
    pares.extend((caracter, " ") for caracter in origen.literal[len(destino.literal) :])
    if set(origen.literal) & {destino_char for _source, destino_char in pares}:
        raise Unsupported("Pendiente: P-JAVA-TRANSLATE-SOLAPADO")
    java = args[0].java if args[0].kind in ("str", "any") else _str(args[0])
    for fuente, reemplazo in pares:
        java += f".replace({_jstr(chr(39) + fuente.replace(chr(39), chr(39) * 2) + chr(39))}, "
        java += f"{_jstr(chr(39) + reemplazo.replace(chr(39), chr(39) * 2) + chr(39))})"
    return E(_guard([args[0]], java), "str")


def _tranwrd(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "tranwrd")
    if args[1].kind != "str" or args[1].literal is None:
        raise Unsupported("Pendiente: P-JAVA-TRANWRD-OBJETIVO-DINAMICO")
    if args[1].literal == "":
        raise Unsupported("Pendiente: P-JAVA-TRANWRD-OBJETIVO-VACIO")
    replacement = args[2]
    if replacement.kind == "null":
        texto_reemplazo = '" "'
    elif replacement.kind == "str" and replacement.literal == "":
        texto_reemplazo = '" "'
    elif replacement.kind == "str":
        texto_reemplazo = replacement.java
    elif replacement.kind == "any":
        texto_reemplazo = (
            f'({replacement.java} == null || {replacement.java}.isEmpty() '
            f'? " " : {replacement.java})'
        )
    else:
        raise Unsupported("Pendiente: P-JAVA-TRANWRD-TIPO-REEMPLAZO")
    body = f"StringHandling.CHANGE({args[0].java}, {args[1].java}, {texto_reemplazo})"
    return E(_guard(args[:2], body), "str")
