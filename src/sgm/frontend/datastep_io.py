"""Lectura conservadora de las sentencias de entrada y salida de DATA step."""

from __future__ import annotations

import re

from sgm.frontend.input_positional import parsear_input_posicional

_OPTIONS = re.compile(
    r"(?i)([a-z_]\w*)\s*(?:=\s*('[^']*(?:''[^']*)*'|\"[^\"]*(?:\"\"[^\"]*)*\"|[^\s()]+))?"
)
_KNOWN_OPTIONS = frozenset(
    {"dsd", "dlm", "delimiter", "firstobs", "flowover", "lrecl", "missover", "truncover"}
)
_INTEGER_OPTIONS = frozenset({"firstobs", "lrecl"})
_INPUT_TOKEN = re.compile(
    r"@@|\$|@|#|\+|/|-|:|\?|\d+\.(?:\d+)?|\d+(?:\.\d+)?|[A-Za-z_&][\w.&]*"
)
_INFORMAT = re.compile(
    r"(?i)^\$?[a-z_]\w*\d+\.$"
    r"|^\$?(?:best|comma|date|datetime|dollar|e|f|hex|ib|mmddyy|n|pd|percent|time|w|yymmdd|z)"
    r"\d+\.\d+$"
    r"|^\$?\d+\.$"
    r"|^\d+\.\d+$"
)
_COLUMN_RANGE = re.compile(r"^\d+$")


def infile_fields(text: str) -> dict:
    """Extrae la referencia, opciones reconocidas y las opciones que requieren revisión."""
    body = re.sub(r"(?is)^infile\s+", "", text.strip(), count=1)
    source, rest = _source(body)
    options: dict[str, object] = {}
    unknown: list[str] = []
    for match in _OPTIONS.finditer(rest):
        name = match.group(1).lower()
        raw_value = match.group(2)
        if name not in _KNOWN_OPTIONS:
            unknown.append(name)
            continue
        if name == "delimiter":
            name = "dlm"
        if raw_value is None:
            value: object = True
        else:
            value = _unquote(raw_value)
            if name in _INTEGER_OPTIONS:
                try:
                    value = int(str(value))
                except ValueError:
                    unknown.append(name)
                    continue
        if name in options and options[name] != value:
            unknown.append(name)
            continue
        options[name] = value
    source_is_path = _quoted(source) and "&" not in source
    return {
        "source": source,
        "source_is_path": source_is_path,
        "source_dynamic": _quoted(source) and not source_is_path,
        "options": options,
        "unsupported_options": sorted(set(unknown)),
        "raw": text,
    }


def input_fields(text: str) -> dict:
    """Reconoce variables, modalidad y tipos que declara el `INPUT` literal."""
    body = re.sub(r"(?is)^input\s+", "", text.strip(), count=1)
    es_posicional, posicional = parsear_input_posicional(text)
    if es_posicional:
        if posicional is None:
            return {"mode": "unknown", "names": [], "raw": text}
        return {
            "mode": "column",
            "names": posicional["names"],
            "fields": posicional["fields"],
            "informats": {
                str(field["name"]): str(field["informat"]) for field in posicional["fields"]
            },
            "raw": text,
        }
    if any(marker in body for marker in ("'", '"', "&", "~", "?")):
        return {"mode": "unknown", "names": [], "raw": text}
    tokens = _INPUT_TOKEN.findall(body)
    mode = "list"
    names: list[str] = []
    types: dict[str, str] = {}
    lengths: dict[str, int] = {}
    informats: dict[str, str] = {}
    current: str | None = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"@", "@@", "+", "#", "/"}:
            mode = "column"
            current = None
            index += 1
            if token in {"@", "+", "#"} and index < len(tokens) and _COLUMN_RANGE.fullmatch(tokens[index]):
                index += 1
            continue
        if token == ":":
            index += 1
            informat, consumed = _informat(tokens, index)
            if current is None or informat is None:
                mode = "unknown"
                continue
            types[current], length = _tipo_informat(informat)
            informats[current] = informat
            if length is not None:
                lengths[current] = length
            index += consumed
            continue
        if token == "?":
            mode = "formatted"
            index += 1
            continue
        if token == "$":
            if current:
                types[current] = "caracter"
            index += 1
            if index < len(tokens) and _INFORMAT.fullmatch(tokens[index]):
                informat = "$" + tokens[index] if not tokens[index].startswith("$") else tokens[index]
                if current:
                    types[current], length = _tipo_informat(informat)
                    informats[current] = informat
                    if length is not None:
                        lengths[current] = length
                index += 1
            continue
        if token.isdigit() and index + 2 < len(tokens) and tokens[index + 1] == "-" and tokens[index + 2].isdigit():
            mode = "column"
            index += 3
            continue
        if token == "-" or (token.endswith(".") and not _INFORMAT.fullmatch(token)):
            mode = "unknown"
            index += 1
            continue
        if _INFORMAT.fullmatch(token):
            mode = "formatted" if mode == "list" else mode
            if current:
                types[current], length = _tipo_informat(token)
                informats[current] = token
                if length is not None:
                    lengths[current] = length
            current = None
            index += 1
            continue
        if re.fullmatch(r"[A-Za-z_&][\w.&]*", token):
            if token.lower() not in {name.lower() for name in names}:
                names.append(token)
            current = token
            types[current] = "numerico"
        index += 1
    resultado = {"mode": mode, "names": names, "raw": text}
    if mode == "list" and types:
        resultado["types"] = types
        if informats:
            resultado["informats"] = informats
        if lengths:
            resultado["lengths"] = lengths
    return resultado


def _informat(tokens: list[str], index: int) -> tuple[str | None, int]:
    """Devuelve un informat literal y cuántos tokens consume desde `index`."""
    if index >= len(tokens):
        return None, 0
    token = tokens[index]
    if token == "$" and index + 1 < len(tokens) and _INFORMAT.fullmatch(tokens[index + 1]):
        return "$" + tokens[index + 1], 2
    if _INFORMAT.fullmatch(token):
        return token, 1
    return None, 0


def _tipo_informat(informat: str) -> tuple[str, int | None]:
    """Tipo y largo demostrados por un informat literal de INPUT en lista."""
    if not informat.startswith("$"):
        return "numerico", None
    ancho = re.search(r"(\d+)\.$", informat)
    return "caracter", int(ancho.group(1)) if ancho else None

def _source(text: str) -> tuple[str, str]:
    if not text:
        return "", ""
    if text[0] not in "'\"":
        match = re.match(r"\S+", text)
        return (match.group(0), text[match.end() :]) if match else ("", "")
    quote = text[0]
    index = 1
    while index < len(text):
        if text[index] == quote:
            if index + 1 < len(text) and text[index + 1] == quote:
                index += 2
                continue
            return text[: index + 1], text[index + 1 :]
        index += 1
    return text, ""


def _quoted(value: str) -> bool:
    return len(value) >= 2 and value[0] == value[-1] and value[0] in "'\""


def _unquote(value: str) -> str:
    text = value.strip()
    if _quoted(text):
        quote = text[0]
        return text[1:-1].replace(quote + quote, quote)
    return text
