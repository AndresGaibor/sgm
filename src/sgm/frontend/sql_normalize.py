"""Normaliza el SQL de PROC SQL de SAS a SQL estándar, para que `sqlglot` lo pueda analizar.

Lo que quita o cambia se anota, para que la traducción no lo pierda en silencio:
- `into :var [separated by "x"]`: variables de macro que recibe el SELECT (`into_vars`).
- `&macro.`: referencias de macro en nombres o valores. Se sustituyen por un identificador
  `mv_<nombre>` y se guarda la vuelta atrás (`macros`).
- `%funcion(`: funciones de macro dentro del SQL. Se sustituyen por `fn_<nombre>(`.
- Operadores de texto de SAS: `eq ne gt lt ge le` (fuera de comillas), `contains`, `is missing`.
- `calculated <col>`: se reduce a `<col>`.
- Opciones de dataset entre paréntesis (`(where=...)`, `(keep=...)`, `(obs=...)`): se quitan.
- Formatos en `input`/`put`, como `8.`: se pasan a cadena.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_QUOTED = "'[^']*'|\"[^\"]*\""  # literal entre comillas simples o dobles
_INTO = re.compile(rf"(?i)\binto\s*:\s*(\w+)(?:\s+separated\s+by\s+({_QUOTED}))?")
_MACRO_REF = re.compile(r"&(\w+)\.?")
_MACRO_FN = re.compile(r"%(\w+)\s*\(")
_CALCULATED = re.compile(r"(?i)\bcalculated\s+(\w+)")
_CONTAINS = re.compile(rf"(?i)(\w+(?:\.\w+)?)\s+contains\s+({_QUOTED})")
_OPTION = re.compile(r"(?i)\b(where|keep|drop|obs|firstobs|rename)\s*=")
_FORMAT_ARG = re.compile(r"(,\s*)(\d+\.\d*)(\s*\))")
_COMPARATORS = {"eq": "=", "ne": "<>", "gt": ">", "lt": "<", "ge": ">=", "le": "<="}


@dataclass
class NormalizedSql:
    text: str
    into_vars: list[tuple[str, str | None]] = field(default_factory=list)  # (variable, separador)
    macros: dict[str, str] = field(default_factory=dict)  # mv_x -> &x
    notes: list[str] = field(default_factory=list)

    def restore(self, name: str) -> str:
        """Nombre SAS original (`lib.&x`) de un nombre con identificadores `mv_` sustituidos."""
        return ".".join(self.macros.get(part, part) for part in name.split("."))


def _outside_quotes(text: str, fn) -> str:
    """Aplica `fn` solo a los trozos de `text` que no están dentro de comillas."""
    parts = re.split(rf"({_QUOTED})", text)
    return "".join(part if i % 2 else fn(part) for i, part in enumerate(parts))


def _strip_options(text: str, notes: list[str]) -> str:
    """Quita `(where=...)` y similares tras un nombre de tabla, con sus paréntesis equilibrados."""
    out = text
    while match := _OPTION.search(out):
        open_at = out.rfind("(", 0, match.start())
        if open_at < 0 or out[open_at + 1 : match.start()].strip():
            # Un `where=` que no abre un grupo de opciones (dentro de un WHERE): no se toca.
            break
        depth, end = 0, None
        for i in range(open_at, len(out)):
            if out[i] == "(":
                depth += 1
            elif out[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            break
        notes.append(f"opción de dataset ({match.group(1).lower()}=...) no se traduce")
        out = out[:open_at] + out[end:]
    return out


def normalize(sql: str) -> NormalizedSql:
    """SQL de PROC SQL en forma estándar, con lo que se quitó anotado."""
    result = NormalizedSql(text=sql)
    text = sql

    for match in _INTO.finditer(text):
        result.into_vars.append((match.group(1), match.group(2)))
    if result.into_vars:
        text = _INTO.sub("", text)
        result.notes.append("INTO: variables de macro recibidas por el SELECT")

    text = _strip_options(text, result.notes)
    # Literal de fecha de SAS (`"01jan2024"d`): se queda como texto; el formato no se traduce.
    text = re.sub(r"(?i)(\"[^\"]*\"|'[^']*')d\b", r"\1", text)
    # Formatos e informatos de columnas en el SELECT (`format=dollar18.2`): solo presentación.
    text = re.sub(r"(?i)\b(?:format|informat)\s*=\s*[\w.$]+", "", text)
    # En SAS, las comillas dobles son literales de texto (no identificadores).
    text = re.sub(r"\"([^\"']*)\"", r"'\1'", text)

    def macro_ref(match: re.Match) -> str:
        placeholder = f"mv_{match.group(1)}"
        result.macros[placeholder] = f"&{match.group(1)}"
        return placeholder

    text = _MACRO_REF.sub(macro_ref, text)
    text = _MACRO_FN.sub(lambda m: f"fn_{m.group(1)}(", text)
    text = _CALCULATED.sub(lambda m: m.group(1), text)
    text = _CONTAINS.sub(lambda m: f"{m.group(1)} LIKE CONCAT('%', {m.group(2)}, '%')", text)

    def operators(part: str) -> str:
        for word, symbol in _COMPARATORS.items():
            part = re.sub(rf"(?i)\b{word}\b", symbol, part)
        part = re.sub(r"(?i)\bis\s+not\s+missing\b", "IS NOT NULL", part)
        part = re.sub(r"(?i)\bis\s+missing\b", "IS NULL", part)
        return part

    text = _outside_quotes(text, operators)
    text = _FORMAT_ARG.sub(lambda m: f"{m.group(1)}'{m.group(2)}'{m.group(3)}", text)
    if result.macros:
        result.notes.append("referencias de macro sustituidas por identificadores")
    result.text = text.strip()
    return result
