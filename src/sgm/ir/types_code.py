"""Tipos que el propio código SAS demuestra (R7): informats, formatos, `put`, `cast` y literales.

Cada regla da un tipo solo si la sentencia lo fija sin ambigüedad. Un tipo que no sale de ninguna
fuente queda como desconocido: nunca se inventa.

- `input(x, w.)` y `input(x, w.d)`: numérico. `Long` si no hay decimales y `w <= 18`; `BigDecimal`
  si hay decimales; `Double` en otro caso.
- Informats de fecha u hora (`yymmdd8.`, `ddmmyy10.`, `datetime20.`...): `Date`.
- `put(x, w.)` o `put(x, $w.)`: `String` de longitud `w`.
- `cast(x as T)` en SQL: el tipo del cast.
- Literales: entero, `Long`; decimal, `Double`; texto entre comillas, `String`. Una operación
  aritmética sobre números: `Double`.
- Declaraciones de un DATA step: `length v $ n;`, `length v n;`, y `format`/`informat` con un
  formato de la lista anterior.

Los tipos de un catálogo o de un encabezado de archivo tienen prioridad: este módulo no los pisa.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

# Los nombres de fecha, la marca de carácter y los umbrales numéricos viven en
# `rules/sas/informats.yaml` (F1.4). Aquí solo se interpretan.
INFORMATS_YAML = Path(__file__).resolve().parents[3] / "rules" / "sas" / "informats.yaml"


def _entrada(id_: str) -> dict:
    entries = yaml.safe_load(INFORMATS_YAML.read_text(encoding="utf-8"))["entries"]
    return next(e for e in entries if e["id"] == id_)


_FECHA = _entrada("fecha")
_CARACTER = _entrada("caracter")
_NUMERICO = _entrada("numerico")

_INFORMAT = re.compile(r"(?i)^(\$?)([a-z]*)(\d*)\.(\d*)$")  # `$10.`, `8.`, `dollar18.2`, `comma12.`
_DATE = re.compile(r"(?i)^(" + "|".join(_FECHA["names"]) + r")\d*\.$")
_CALL = re.compile(r"(?i)^(input|put)\s*\(\s*(.+?)\s*,\s*(\$?[a-z]*\d*\.\d*)\s*\)$")
_CAST = re.compile(r"(?i)^cast\s*\(.*\bas\s+(\w+)\s*(?:\(\s*(\d+)[^)]*\))?\s*\)$")
_ARITHMETIC = re.compile(r"^[\d\s.+\-*/()]+$")
_NUMERIC_LITERAL = re.compile(r"^[+-]?\d+$")
_DECIMAL_LITERAL = re.compile(r"^[+-]?\d*\.\d+$")
_TEXT_LITERAL = re.compile(r"^(['\"]).*\1$", re.S)
_BOOLEAN_OPERATOR = re.compile(
    r"(?i)\b(?:and|or|not|in|between)\b|<=|>=|<>|~=|¬=|(?<![<>=])=(?!=)|(?<![<>=])[<>](?![=>])"
)
_QUOTED_VALUE = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", re.S)
_LENGTH_ITEM = re.compile(r"(\w+)\s+(\$?)\s*(\d+)")
_FORMAT_ITEM = re.compile(r"(\w+)\s+(\$?[a-zA-Z]*\d*\.\d*)")
_CAST_TYPES = {
    "int": "Integer",
    "integer": "Integer",
    "smallint": "Integer",
    "tinyint": "Integer",
    "bigint": "Long",
    "decimal": "BigDecimal",
    "numeric": "BigDecimal",
    "float": "Double",
    "double": "Double",
    "real": "Double",
    "varchar": "String",
    "char": "String",
    "string": "String",
    "date": "Date",
    "timestamp": "Date",
}


# Funciones de SAS cuyo resultado es siempre de carácter o siempre numérico (por definición).
_CHARACTER_FUNCTIONS = frozenset(
    {
        "compress",
        "strip",
        "trim",
        "trimn",
        "left",
        "right",
        "upcase",
        "lowcase",
        "substr",
        "substrn",
        "cat",
        "cats",
        "catt",
        "catx",
        "compbl",
        "tranwrd",
    }
)
_NUMERIC_FUNCTIONS = frozenset(
    {"int", "round", "abs", "sum", "max", "min", "mean", "count", "length", "index", "sqrt"}
)


@dataclass(frozen=True)
class CodeType:
    type: str
    length: int | None = None


def numeric_type(_width: int, decimals: int) -> CodeType:
    """Tipo conservador: el ancho no prueba integralidad; `d` sí fija escala decimal."""
    if decimals > 0:
        return CodeType(_NUMERICO["decimals_type"])
    return CodeType(_NUMERICO["no_decimals_type"])


def informat_type(spec: str) -> CodeType | None:
    """Tipo que fija un informat o formato (`8.`, `30.2`, `$10.`, `yymmdd8.`). None si no fija."""
    text = spec.strip().lower()
    if _DATE.match(text):
        return CodeType(_FECHA["type"])
    match = _INFORMAT.match(text)
    if not match:
        return None
    dollar, name, width_text, decimals_text = match.groups()
    width = int(width_text or 0)
    if dollar or name.startswith(_CARACTER["prefix"]):
        return CodeType(_CARACTER["type"], width or None)
    if name and name not in _NUMERICO["names"]:
        return None
    return numeric_type(width, int(decimals_text or 0))


_CONDICIONAL = re.compile(r"(?is)^\s*case\b")


def expression_type(expression: str) -> CodeType | None:
    """Tipo de expresiones fijado por código: entrada, literal, aritmética o predicado."""
    text = expression.strip()
    if _CONDICIONAL.match(text):
        # Un CASE devuelve el valor de una rama, no un predicado: sus condiciones (IS MISSING, AND)
        # no hacen booleana la expresión entera.
        return None
    sin_literales = _QUOTED_VALUE.sub("''", text)
    if _BOOLEAN_OPERATOR.search(sin_literales) or _single_call(sin_literales) == "missing":
        return CodeType("Boolean")
    if _TEXT_LITERAL.match(text):
        return CodeType("String")
    if _NUMERIC_LITERAL.match(text):
        return CodeType("Long")
    if _DECIMAL_LITERAL.match(text):
        return CodeType("Double")
    if match := _CALL.match(text):
        fn, spec = match.group(1).lower(), match.group(3)
        if fn == "input":
            return informat_type(spec)
        width = re.match(r"^\$?(\d*)", spec).group(1)
        return CodeType("String", int(width) if width else None)
    if match := _CAST.match(text):
        base = _CAST_TYPES.get(match.group(1).lower())
        if base is None:
            return None
        return CodeType(base, int(match.group(2)) if match.group(2) else None)
    if _ARITHMETIC.match(text) and re.search(r"[+\-*/]", text) and re.search(r"\d", text):
        return CodeType("Double")
    if call := _single_call(text):
        if call in _CHARACTER_FUNCTIONS:
            return CodeType("String")
        if call in _NUMERIC_FUNCTIONS:
            return CodeType("Double")
    return None


def _single_call(text: str) -> str | None:
    """Nombre en minúsculas si el texto es una sola llamada `nombre(...)`; None si no."""
    match = re.match(r"^([A-Za-z_]\w*)\s*\(", text)
    if not match:
        return None
    depth = 0
    for index in range(match.end() - 1, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return match.group(1).lower() if index == len(text) - 1 else None
    return None


def declared_types(declarations: list[tuple[str, str]]) -> dict[str, CodeType]:
    """Tipos de las declaraciones de un DATA step: [(sentencia, cuerpo)] -> {columna: tipo}.

    Acepta `length v $ n;`, `length v n;`, `format v fmt;` e `informat v fmt;`. Lo que no se
    entiende no entra.
    """
    found: dict[str, CodeType] = {}
    for kind, body in declarations:
        if kind == "length":
            for name, dollar, number in _LENGTH_ITEM.findall(body):
                found[name.lower()] = (
                    CodeType("String", int(number)) if dollar else numeric_type(int(number), 0)
                )
        elif kind in ("format", "informat"):
            for name, spec in _FORMAT_ITEM.findall(body):
                declared = informat_type(spec)
                if declared is not None:
                    found.setdefault(name.lower(), declared)
    return found
