"""Parser conservador para `INPUT` de columna y formateado con campos de ancho fijo."""

from __future__ import annotations

import re

_TOKEN = re.compile(r"\s*(\$?[A-Za-z_]*\d+\.\d*|@@|@|\$|\d+|[A-Za-z_]\w*|[-+/#:])")
_INFORMAT = re.compile(r"(?i)^\$?([A-Za-z_]*)(\d+)\.(\d*)$")
_IDENTIFIER = re.compile(r"^[A-Za-z_]\w*$")
_RANGE = re.compile(r"\d+\s*-\s*\d+")


def parsear_input_posicional(text: str) -> tuple[bool, dict | None]:
    """Devuelve si la sentencia es posicional y sus campos si el subconjunto es literal.

    Acepta punteros absolutos `@n`, informats con ancho y rangos de columnas inclusivos.
    Otros controles de puntero y expresiones se conservan como no reconocidos.
    """
    body = re.sub(r"(?is)^input\s+", "", text.strip(), count=1)
    body = re.sub(r";\s*$", "", body)
    matches = list(_TOKEN.finditer(body))
    if not matches or "".join(match.group(1) for match in matches).replace(" ", "") == "":
        return False, None
    tokens = [match.group(1) for match in matches]
    consumed_text = "".join(match.group(0) for match in matches).strip()
    positional = any(token in {"@", "@@", "+", "#", "/"} for token in tokens) or any(
        _RANGE.fullmatch(f"{tokens[index]}-{tokens[index + 2]}")
        for index in range(len(tokens) - 2)
        if tokens[index].isdigit() and tokens[index + 1] == "-" and tokens[index + 2].isdigit()
    )
    if not positional:
        return False, None
    if re.sub(r"\s+", "", consumed_text) != re.sub(r"\s+", "", body):
        return True, None

    fields: list[dict[str, object]] = []
    names: set[str] = set()
    cursor = 1
    index = 0
    while index < len(tokens):
        explicit_start: int | None = None
        if tokens[index] == "@":
            if index + 1 >= len(tokens) or not tokens[index + 1].isdigit():
                return True, None
            explicit_start = int(tokens[index + 1])
            if explicit_start < 1:
                return True, None
            index += 2
        elif tokens[index] in {"@@", "+", "#", "/"}:
            return True, None

        if index >= len(tokens) or not _IDENTIFIER.fullmatch(tokens[index]):
            return True, None
        name = tokens[index]
        if name.casefold() in names:
            return True, None
        names.add(name.casefold())
        index += 1

        is_character = False
        if index < len(tokens) and tokens[index] == "$":
            is_character = True
            index += 1

        informat: str | None = None
        start = explicit_start if explicit_start is not None else cursor
        width: int | None = None
        if index < len(tokens) and _INFORMAT.fullmatch(tokens[index]):
            informat = tokens[index]
            info = _INFORMAT.fullmatch(informat)
            assert info is not None
            width = int(info.group(2))
            is_character = informat.startswith("$") or info.group(1).casefold().startswith("char")
            index += 1
        elif index < len(tokens) and tokens[index].isdigit():
            range_start = int(tokens[index])
            if index + 2 < len(tokens) and tokens[index + 1] == "-" and tokens[index + 2].isdigit():
                end = int(tokens[index + 2])
                if end < range_start:
                    return True, None
                start, width = range_start, end - range_start + 1
                index += 3
            else:
                start, width = range_start, 1
                index += 1
            informat = f"${width}." if is_character else f"{width}."
        else:
            return True, None

        if width is None or width < 1:
            return True, None
        fields.append({"name": name, "start": start, "width": width, "informat": informat})
        cursor = start + width

    return True, {"fields": fields, "names": [str(field["name"]) for field in fields]}


__all__ = ["parsear_input_posicional"]
