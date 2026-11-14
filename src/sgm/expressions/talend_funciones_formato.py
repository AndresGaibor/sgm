"""Conversión INPUT/PUT y limpieza de expresiones para el traductor Talend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

import re

from sgm.expressions.talend_base import E, Unsupported, _date_pattern, _guard, _jstr, _need
from sgm.expressions.talend_lexer import _collapse_whitespace_outside_strings
from sgm.formatos.informat_fecha import informat_fecha_soportado
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
            if not informat_fecha_soportado(spec):
                raise Unsupported("informat de fecha fuera del subconjunto documentado")
            return E(_input_fecha(base, args[0].java), "date")
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


def _input_fecha(base: str, expression: str) -> str:
    """Expresión Java estricta para las formas de fecha de cuatro dígitos documentadas."""
    source = f"({expression} == null ? null : StringHandling.TRIM({expression}))"
    compact = f'{source}.replace("-", "").replace("/", "")'
    pending_year = (
        'java.util.Objects.requireNonNull((java.sql.Date) null, "P-YEARCUTOFF-EXPLICITO")'
    )
    pending_style = (
        'java.util.Objects.requireNonNull((java.sql.Date) null, "P-ANYDTDTE-DATESTYLE")'
    )

    def _date_value(year: str, month: str, day: str, valid_month: str) -> str:
        valid = f"java.time.YearMonth.of({year}, {month}).isValidDay({day})"
        date = f"java.sql.Date.valueOf(java.time.LocalDate.of({year}, {month}, {day}))"
        return f"({valid_month} ? ({valid} ? {date} : null) : null)"

    empty = f'({source} == null || {source}.isEmpty() || {source}.equals("."))'
    if base in {"yymmdd", "anydtdte"}:
        month_valid = f'{compact}.substring(4, 6).matches("0[1-9]|1[0-2]")'
        four_year = (
            f'{source}.matches("[0-9]{{8}}|[0-9]{{4}}[-/][0-9]{{2}}[-/][0-9]{{2}}")'
        )
        year = f"Integer.parseInt({compact}.substring(0, 4))"
        month = f"Integer.parseInt({compact}.substring(4, 6))"
        day = f"Integer.parseInt({compact}.substring(6, 8))"
        parsed = _date_value(year, month, day, month_valid)
        if base == "anydtdte":
            iso = f'{source}.matches("[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}")'
            ambiguous = f'{source}.matches("[0-9]{{1,2}}[-/][0-9]{{1,2}}[-/][0-9]{{4}}")'
            two_digit = f'{source}.matches("[0-9]{{1,2}}[-/][0-9]{{1,2}}[-/][0-9]{{2}}")'
            return f"({empty} ? null : ({two_digit} ? {pending_year} : ({ambiguous} ? {pending_style} : ({iso} ? {parsed} : null))))"
        two_digit = (
            f'{source}.matches("[0-9]{{6}}|[0-9]{{2}}[-/][0-9]{{2}}[-/][0-9]{{2}}")'
        )
        return f"({empty} ? null : ({two_digit} ? {pending_year} : ({four_year} ? {parsed} : null)))"
    if base == "ddmmyy":
        two_digit = (
            f'{source}.matches("[0-9]{{6}}|[0-9]{{2}}[-/][0-9]{{2}}[-/][0-9]{{2}}")'
        )
        month_valid = f'{compact}.substring(2, 4).matches("0[1-9]|1[0-2]")'
        four_year = (
            f'{source}.matches("[0-9]{{8}}|[0-9]{{2}}[-/][0-9]{{2}}[-/][0-9]{{4}}")'
        )
        day = f"Integer.parseInt({compact}.substring(0, 2))"
        month = f"Integer.parseInt({compact}.substring(2, 4))"
        year = f"Integer.parseInt({compact}.substring(4, 8))"
        parsed = _date_value(year, month, day, month_valid)
        return f"({empty} ? null : ({two_digit} ? {pending_year} : ({four_year} ? {parsed} : null)))"
    # DATEw. accepts an English three-letter month; a two-digit year needs explicit YEARCUTOFF.
    two_digit = f'{source}.matches("[0-9]{{2}}[A-Za-z]{{3}}[0-9]{{2}}")'
    names = "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC"
    four_year = f'{source}.matches("(?i)[0-9]{{2}}({names})[0-9]{{4}}")'
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    month = "(" + " : ".join(
        f'{source}.substring(2, 5).equalsIgnoreCase("{name}") ? {index}'
        for index, name in enumerate(months, 1)
    ) + " : 0)"
    year = f"Integer.parseInt({source}.substring(5, 9))"
    day = f"Integer.parseInt({source}.substring(0, 2))"
    parsed = _date_value(year, month, day, four_year)
    return f"({empty} ? null : ({two_digit} ? {pending_year} : ({four_year} ? {parsed} : null)))"


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
