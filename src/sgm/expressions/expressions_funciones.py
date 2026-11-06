"""Funciones SAS de las expresiones: traducción de cada función a Java (tabla `_FUNCTIONS`)."""

import re

from sgm.expressions.expressions_base import (
    _Unsupported,
)


def _guard(value: str, expr: str) -> str:
    """Función con guarda de nulo: un argumento missing da null (como en SAS, el resultado es missing)."""
    return f"({value} == null ? null : {expr})"


def _f_substr(args: list[str]) -> str:
    if len(args) != 3:
        raise _Unsupported("substr() sin los tres argumentos (cadena, inicio, longitud)")
    text, start, length = args
    first = str(int(start) - 1) if re.fullmatch(r"\d+", start) else f"({start} - 1)"
    return _guard(text, f"{text}.substring({first}, {first} + {length})")


def _f_round(args: list[str]) -> str:
    if len(args) not in (1, 2):
        raise _Unsupported("round() con más de dos argumentos")
    value = args[0]
    unit = args[1] if len(args) == 2 else "1"
    rounded = value if unit == "1" else f"({value} / {unit})"
    rounded = f"Math.copySign(Math.floor(Math.abs({rounded}) + 0.5), {rounded})"
    if unit != "1":
        rounded = f"({rounded} * {unit})"
    return _guard(value, f"Double.valueOf((double) {rounded})")


def _f_length(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("length() con más de un argumento")
    return f"({args[0]} == null ? 0 : {args[0]}.length())"


def _f_abs(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("abs() con más de un argumento")
    return _guard(args[0], f"Math.abs({args[0]})")


def _f_int(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("int() con más de un argumento")
    return _guard(args[0], f"((long) ({args[0]}))")


def _f_cats(args: list[str]) -> str:
    if not args:
        raise _Unsupported("cats() sin argumentos")
    parts = [f'({arg} == null ? "" : String.valueOf({arg}))' for arg in args]
    return "(" + " + ".join(parts) + ")"


def _f_if(args: list[str]) -> str:
    """ifn/ifc(condición, si verdadera, si falsa): operador condicional de Java."""
    if len(args) != 3:
        raise _Unsupported("ifn()/ifc() sin los tres argumentos (condición, verdadero, falso)")
    condition, when_true, when_false = args
    return f"({condition} ? {when_true} : {when_false})"


def _f_min(args: list[str]) -> str:
    if len(args) < 2:
        raise _Unsupported("min() con menos de dos argumentos")
    result = args[0]
    for arg in args[1:]:
        result = f"Math.min({result}, {arg})"
    return result


def _f_max(args: list[str]) -> str:
    if len(args) < 2:
        raise _Unsupported("max() con menos de dos argumentos")
    result = args[0]
    for arg in args[1:]:
        result = f"Math.max({result}, {arg})"
    return result


def _f_coalesce(args: list[str]) -> str:
    """Primer argumento no missing (como coalesce de SAS)."""
    if not args:
        raise _Unsupported("coalesce() sin argumentos")
    result = args[-1]
    for arg in reversed(args[:-1]):
        result = f"({arg} != null ? {arg} : {result})"
    return result


def _f_compress(args: list[str]) -> str:
    """compress(texto) quita los blancos; con lista de caracteres no hay equivalente simple."""
    if len(args) != 1:
        raise _Unsupported("compress() con lista de caracteres: sin equivalente simple")
    return _guard(args[0], args[0] + '.replaceAll(" ", "")')


def _f_index(args: list[str]) -> str:
    """index(texto, subcadena): posición de 1 base, 0 si no está (como en SAS)."""
    if len(args) != 2:
        raise _Unsupported("index() con más de dos argumentos")
    text, sub = args
    return _guard(text, f"({text}.indexOf({sub}) + 1)")


_NUMERIC_FORMAT = re.compile(r'"(?:best|comma)\d*\.\d*"', re.IGNORECASE)


#: Formatos de fecha de SAS y su patrón Java (SimpleDateFormat) para TalendDate.
_DATE_FORMATS = {
    "yymmdd8.": "yyyyMMdd",
    "yymmdd10.": "yyyy-MM-dd",
    "ddmmyy10.": "dd/MM/yyyy",
    "mmddyy10.": "MM/dd/yyyy",
    "date9.": "ddMMMyyyy",
    "datetime20.": "ddMMMyyyy:HH:mm:ss",
}
#: Intervalos de intnx/intck y su unidad de TalendDate.
_INTERVALS = {"day": "dd", "week": "dd", "month": "mm", "year": "yy"}


def _date_format(literal: str) -> str | None:
    return _DATE_FORMATS.get(literal.strip('"').lower())


def _f_mdy(args: list[str]) -> str:
    if len(args) != 3:
        raise _Unsupported("mdy() sin los tres argumentos (mes, día, año)")
    month, day, year = args
    guard = f"({month} == null || {day} == null || {year} == null)"
    text = f'String.format("%04d-%02d-%02d", {year}, {month}, {day})'
    return f'({guard} ? null : TalendDate.parseDate("yyyy-MM-dd", {text}))'


def _f_datepart(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("datepart() con más de un argumento (solo la parte de fecha)")
    value = args[0]
    return _guard(
        value, f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-MM-dd", {value}))'
    )


def _f_intnx(args: list[str]) -> str:
    if len(args) not in (3, 4):
        raise _Unsupported("intnx() con intervalo, fecha y desplazamiento (alineación opcional)")
    interval, value, step = args[0], args[1], args[2]
    alignment = args[3].strip('"').lower() if len(args) == 4 else "same"
    name = interval.strip('"').lower()
    unit = _INTERVALS.get(name)
    if unit is None:
        raise _Unsupported(f"intnx() con intervalo {name} sin equivalente")
    if alignment not in ("same", "begin"):
        raise _Unsupported(f"intnx() con alineación {alignment}: solo same y begin")
    amount = f"({step}) * 7" if name == "week" else step
    moved = f'TalendDate.addDate({value}, (int) ({amount}), "{unit}")'
    if alignment == "begin" and unit == "mm":
        moved = f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-MM-01", {moved}))'
    elif alignment == "begin" and unit == "yy":
        moved = f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-01-01", {moved}))'
    return _guard(value, moved)


def _f_intck(args: list[str]) -> str:
    if len(args) != 3:
        raise _Unsupported("intck() sin los tres argumentos (intervalo, inicio, fin)")
    interval, start, end = args
    name = interval.strip('"').lower()
    unit = _INTERVALS.get(name)
    if unit is None:
        raise _Unsupported(f"intck() con intervalo {name} sin equivalente")
    divisor = " / 7" if name == "week" else ""
    return _guard(start, f'(TalendDate.diffDate({end}, {start}, "{unit}"){divisor})')


def _f_today(args: list[str]) -> str:
    if args:
        raise _Unsupported("today() sin argumentos")
    return "TalendDate.getCurrentDate()"


def _f_date_part(part: str):
    def build(args: list[str]) -> str:
        if len(args) != 1:
            raise _Unsupported(f"{part.lower()}() con más de un argumento")
        return _guard(args[0], f'TalendDate.getPartOfDate("{part}", {args[0]})')

    return build


def _f_input(args: list[str]) -> str:
    """input(texto, formato numérico): conversión a número; las fechas de SAS quedan fuera (sin equivalente simple)."""
    if len(args) == 2 and _date_format(args[1]):
        text = args[0]
        return _guard(text, f'TalendDate.parseDate("{_date_format(args[1])}", {text})')
    if len(args) != 2 or not _NUMERIC_FORMAT.fullmatch(args[1]):
        raise _Unsupported("input() solo con formato numérico (best./comma.)")
    return _guard(args[0], f"Double.parseDouble({args[0]})")


def _f_put(args: list[str]) -> str:
    """put(número, formato numérico): conversión a texto."""
    if len(args) == 2 and _date_format(args[1]):
        return _guard(args[0], f'TalendDate.formatDate("{_date_format(args[1])}", {args[0]})')
    if len(args) != 2 or not _NUMERIC_FORMAT.fullmatch(args[1]):
        raise _Unsupported("put() solo con formato numérico (best./comma.)")
    return _guard(args[0], f"String.valueOf({args[0]})")


_FUNCTIONS = {
    "mdy": _f_mdy,
    "datepart": _f_datepart,
    "intnx": _f_intnx,
    "intck": _f_intck,
    "today": _f_today,
    "year": _f_date_part("YEAR"),
    "month": _f_date_part("MONTH"),
    "day": _f_date_part("DAY_OF_MONTH"),
    "input": _f_input,
    "put": _f_put,
    "min": _f_min,
    "max": _f_max,
    "coalesce": _f_coalesce,
    "compress": _f_compress,
    "index": _f_index,
    "ifn": _f_if,
    "ifc": _f_if,
    "substr": _f_substr,
    "round": _f_round,
    "length": _f_length,
    "abs": _f_abs,
    "int": _f_int,
    "cats": _f_cats,
    "cat": _f_cats,
}
_FUNCTION_WARNINGS = {
    "today": [
        "today(): en SAS es días desde 1960; en Talend es un Date: validar al comparar con fechas SAS"
    ],
    "year": [
        "year/month/day(): sobre un Date de Talend; con fecha SAS numérica validar la conversión de época"
    ],
    "month": [
        "year/month/day(): sobre un Date de Talend; con fecha SAS numérica validar la conversión de época"
    ],
    "day": [
        "year/month/day(): sobre un Date de Talend; con fecha SAS numérica validar la conversión de época"
    ],
    "mdy": ["mdy(): devuelve un Date de Talend; con missing en mes, día o año devuelve null"],
    "datepart": [
        "datepart(): quita la hora; validar con datetimes SAS (época 1960 frente a Date de Talend)"
    ],
    "intnx": [
        "intnx(): alineación same/begin; end no se traduce. Validar la unidad con datos reales"
    ],
    "intck": [
        "intck(): cuenta fronteras de unidad como SAS; diffDate devuelve la diferencia de la unidad, validar el signo"
    ],
    "input": [
        "input(): convierte texto con el formato indicado; un texto no válido lanza excepción"
    ],
    "put": ["put(): convierte un valor con el formato indicado a texto"],
    "min": ["min()/max(): con missing en Java el resultado es null; SAS ignora el missing"],
    "max": ["min()/max(): con missing en Java el resultado es null; SAS ignora el missing"],
    "coalesce": ["coalesce(): el orden de los argumentos se conserva"],
    "compress": ["compress(): quita solo blancos (espacios, tabuladores, saltos)"],
    "index": ["index(): 0 si la subcadena no aparece, como en SAS"],
    "ifn": [
        "ifn()/ifc(): con missing en la condición Java la evalúa como falsa; validar con datos"
    ],
    "ifc": [
        "ifn()/ifc(): con missing en la condición Java la evalúa como falsa; validar con datos"
    ],
    "substr": ["substr(): posición de 1 base convertida a 0; con cadena más corta puede fallar"],
    "round": ["round(): redondeo al múltiplo indicado (la mitad sube, como en SAS)"],
    "length": ["length(): en SAS los blancos finales cuentan; revisar con datos reales"],
    "int": ["int(): trunca hacia cero, como en SAS"],
    "cats": [
        "cats()/cat(): no quita blancos finales; los numéricos se convierten con String.valueOf"
    ],
    "cat": [
        "cats()/cat(): no quita blancos finales; los numéricos se convierten con String.valueOf"
    ],
}


TEXT_TYPE_WARNING = "tipo no confirmado: se asumió texto; confirmar con el esquema real"
