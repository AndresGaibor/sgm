"""Conversión INPUT/PUT y limpieza de expresiones para el traductor Talend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

import re

from sgm.expressions.talend_base import E, Unsupported, _date_pattern, _guard, _jstr, _need
from sgm.expressions.talend_lexer import _collapse_whitespace_outside_strings
from sgm.ir.types_code import informat_type


def _input(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "input")
    if args[1].literal is None:
        raise Unsupported("informat dinámico o no literal; queda pendiente de resolución")
    spec = args[1].literal.strip()
    fmt = spec.lower().rstrip(".")
    tipo = informat_type(spec)
    if tipo is None:
        raise Unsupported("informat no soportado; queda pendiente de revisión")
    base = "e8601da" if fmt.startswith("e8601da") else re.match(r"^\$?([a-z]*)", fmt).group(1)
    if tipo.type == "Date":
        if base != "e8601da":
            raise Unsupported(
                "informat de fecha requiere opciones de fecha SAS y formato de entrada confirmado "
                "(YEARCUTOFF, DATESTYLE o locale)"
            )
        pattern = _date_pattern(base)
        return E(
            f"TalendDate.parseDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "date"
        )
    if tipo.type == "String":
        return E(args[0].java, "str")
    if base in ("comma", "dollar"):
        decimals = int(re.search(r"\.(\d+)$", fmt).group(1) or 0) if "." in fmt else 0
        source = f"StringHandling.TRIM({args[0].java})"
        clean = source + (
            '.replace(",", "").replace(" ", "").replace("$", "").replace("%", "")'
            '.replace("-", "").replace("(", "").replace(")", "")'
        )
        signed = f'({source}.startsWith("(") ? "-" + {clean} : {clean})'
        allowed_pattern = chr(34) + r"[0-9,$%() .-]+" + chr(34)
        allowed = f"{source}.matches({_jstr(allowed_pattern)})"
        parentheses = (
            f'(!{source}.contains("(") || '
            f'({source}.startsWith("(") && {source}.indexOf("(", 1) == -1))'
        )
        numeric_pattern = chr(34) + r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)" + chr(34)
        numeric = f"{clean}.matches({_jstr(numeric_pattern)})"
        value = (
            f"new java.math.BigDecimal({signed}).movePointLeft("
            f'{clean}.contains({_jstr(chr(34) + "." + chr(34))}) ? 0 : {decimals})'
        )
        parsed = value if decimals else f"Double.valueOf(({value}).doubleValue())"
        return E(
            _guard([args[0]], f"({allowed} && {parentheses} && {numeric} ? {parsed} : null)"),
            "num",
        )
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
    raise Unsupported("put con formato no soportado; queda pendiente de revisión")


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
