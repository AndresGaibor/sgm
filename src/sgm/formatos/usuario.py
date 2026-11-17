"""Localiza el argumento literal de PUT sin modificar cadenas ni otras funciones."""

from __future__ import annotations

import re
from collections.abc import Collection

_TOKENS = re.compile(
    r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|/\*.*?\*/|--[^\n]*|"
    r"\$[A-Za-z_]\w*\.|[A-Za-z_]\w*|[^\s]", re.S
)


def normalize_user_put(text: str, names: Collection[str]) -> str:
    """Entrecomilla solo $nombre. como segundo argumento de PUT y declarado en el plan."""
    tokens = list(_TOKENS.finditer(text))
    stack: list[list] = []
    changes = []
    previous = ""
    for index, token in enumerate(tokens):
        value = token.group()
        if value.startswith(("/*", "--")):
            continue
        if value == "(":
            stack.append([previous.casefold(), 0])
        elif value == ")":
            if stack:
                stack.pop()
        elif value == "," and stack:
            stack[-1][1] += 1
        elif (
            stack and stack[-1] == ["put", 1]
            and value.startswith("$") and value[:-1].casefold() in names
            and previous == "," and index + 1 < len(tokens)
            and tokens[index + 1].group() == ")"
        ):
            changes.append((token.start(), token.end(), repr(value[:-1].casefold())))
        previous = value
    for start, end, replacement in reversed(changes):
        text = text[:start] + replacement + text[end:]
    return text
