"""Constructores Talend para funciones SAS de texto."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

import re

from sgm.expressions.talend_base import E, Unsupported, _guard, _jstr, _need, _num, _str


def _strfn(template: str, arity: int = 1):
    """Función de texto que, ante un perdido (null), devuelve null."""

    def build(_p: _P, args: list[E]) -> E:
        _need(args, arity, arity, template)
        out = template.format(*[a.java for a in args])
        return E(_guard(args[:1], out) if args[0].kind != "str" else out, "str")

    return build


def _propcase(_p: _P, args: list[E]) -> E:
    _need(args, 1, 2, "propcase")
    raise Unsupported(
        "Pendiente: P-JAVA-PROPCASE; Talend no ofrece una rutina equivalente con delimitadores SAS"
    )


def _repeat(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "repeat")
    if args[1].kind != "num" or not re.fullmatch(r"\d+", args[1].java):
        raise Unsupported(
            "Pendiente: P-REPEAT-N-ENTERO; solo se traduce un literal entero no negativo"
        )
    return _strfn('(new String(new char[{1} + 1]).replace("\\0", {0}))', 2)(p, args)


def _cat(trim: bool, sep: bool = False, trailing_only: bool = False):
    def build(_p: _P, args: list[E]) -> E:
        if sep:
            if len(args) < 2:
                raise Unsupported("catx necesita separador y valores")
            glue, items = args[0], args[1:]
        else:
            glue, items = E('""', "str"), args
        trim_fn = "StringHandling.RTRIM" if trailing_only else "StringHandling.TRIM"
        parts = [f"{trim_fn}({_str(i)})" if trim or trailing_only else _str(i) for i in items]
        if sep:  # catx omite los vacíos
            return E(
                "String.join("
                + _str(glue)
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
        prefijo = _jstr(chr(34) + f"^[{delims}]+" + chr(34))
        separador = _jstr(chr(34) + f"[{delims}]+" + chr(34))
    else:
        delims = r"\s!$%&()*+,\-./;\x3c^"
        prefijo = _jstr(chr(34) + f"^[{delims}]+" + chr(34))
        separador = _jstr(chr(34) + f"[{delims}]+" + chr(34))
    p.warnings.add("scan: los delimitadores consecutivos cuentan como uno, como en SAS")
    tokens = f'{args[0].java}.replaceAll({prefijo}, "").split({separador})'
    # Con delimitadores declarados o cuenta negativa se indexa el arreglo; el `skip` no sabe contar
    # desde el final, y sin delimitadores el flujo perezoso es el que ya se emitía.
    if explicito or n < 0:
        index = str(n - 1) if n > 0 else f"Math.abs({tokens}.length - {abs(n)})"
        return E(
            _guard([args[0]], f"java.util.Arrays.stream({tokens}).skip({index}).findFirst().orElse(\"\")"), "str"
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
