"""Normaliza el SQL de PROC SQL de SAS a SQL estándar, para que `sqlglot` lo pueda analizar.

Lo que quita o cambia se anota, para que la traducción no lo pierda en silencio:
- `into :var [separated by "x"]`: variables de macro que recibe el SELECT (`into_vars`).
- `&macro.`: referencias de macro en nombres o valores. Se sustituyen por un identificador
  `mv_<nombre>` y se guarda la vuelta atrás (`macros`).
- `%funcion(`: funciones de macro dentro del SQL. Se sustituyen por `fn_<nombre>(`.
- Operadores de texto de SAS: `eq ne gt lt ge le` (fuera de comillas), `contains`, `is missing`.
- Name literals de SAS (`'Un Nombre Con Espacios'n`): se convierten a identificador entre comillas dobles.
- `LABEL=...`: solo presentación; se quita.
- Informatos en argumentos de `input`/`put` (`w1.`, `datetime20.`): se pasan a cadena.
- `.` como literal de faltante (`x = .`, `x <> .`): se reescribe a `IS NULL` / `IS NOT NULL`.
- `^=` y `NOT =`: se reescriben a `<>`.
- `contains` con operando no literal: se reescribe a `LIKE CONCAT('%', ..., '%')`.
- `calculated <col>`: se reduce a `<col>`.
- Opciones de dataset entre paréntesis (`(where=...)`, `(keep=...)`, `(obs=...)`): se quitan.
- Formatos en `input`/`put`, como `8.`: se pasan a cadena.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_QUOTED = "'[^']*'|\"[^\"]*\""  # literal entre comillas simples o dobles
_INTO = re.compile(
    rf"(?i)\binto\s*((?::\s*\w+\s*,?\s*)+)"  # una o más variables :x, :y
    rf"(?:trimmed\b\s*)?(?:separated\s+by\s+({_QUOTED})\s*)?(?:trimmed\b\s*)?"
)
_INTO_NAME = re.compile(r":\s*(\w+)")
_MACRO_REF = re.compile(r"&(\w+)\.?")
_MACRO_FN = re.compile(r"%(\w+)\s*\(")
_CALCULATED = re.compile(r"(?i)\bcalculated\s+(\w+)")
_NAME_LITERAL = re.compile(r"'((?:[^']|'')*)'n\b", re.IGNORECASE)
_LABEL = re.compile(rf"(?i)\blabel\s*=\s*({_QUOTED})")
_INFORMAT_ARG = re.compile(r"([(,]\s*)(\$?[A-Za-z_$][A-Za-z0-9_$]*[0-9]+\.[0-9]*|\$[0-9]+\.[0-9]*)(\s*(?=[,)]))")
_MISSING_LITERAL = re.compile(r"(<>|=)\s*\.(?![\dA-Za-z_$])")
_NOT_EQ = re.compile(r"(?i)\bnot\s*=")
_CONTAINS_WORD = re.compile(r"(?i)\bcontains\b")
_OPTION = re.compile(r"(?i)\b(where|keep|drop|obs|firstobs|rename)\s*=")
_FORMAT_ARG = re.compile(r"(,\s*)(\d+\.\d*)(\s*\))")
_MULTIARG_ROW_FUNCTION = re.compile(r"(?i)\b(sum|min|max|mean)\b")
_COMPARATORS = {"eq": "=", "ne": "<>", "gt": ">", "lt": "<", "ge": ">=", "le": "<="}


@dataclass
class NormalizedSql:
    text: str
    into_vars: list[tuple[str, str | None]] = field(default_factory=list)  # (variable, separador)
    macros: dict[str, str] = field(default_factory=dict)  # mv_x -> &x
    notes: list[str] = field(default_factory=list)
    row_functions: dict[str, str] = field(default_factory=dict)  # marcador interno -> nombre SAS

    def restore(self, name: str) -> str:
        """Nombre SAS original (`lib.&x`) de un nombre con identificadores `mv_` sustituidos."""
        return ".".join(self.macros.get(part, part) for part in name.split("."))


def _outside_quotes(text: str, fn) -> str:
    """Aplica `fn` al código SQL y conserva literalmente cadenas y comentarios."""
    output: list[str] = []
    last = 0
    for start, end in _protected_ranges(text):
        output.append(fn(text[last:start]))
        output.append(text[start:end])
        last = end
    output.append(fn(text[last:]))
    return "".join(output)


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


def _protected_ranges(text: str) -> list[tuple[int, int]]:
    """Rangos de literales y comentarios; primero reconoce comentario, luego sus comillas."""
    ranges: list[tuple[int, int]] = []
    i = 0
    while i < len(text):
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = len(text) if end < 0 else end + 2
            ranges.append((i, end))
            i = end
            continue
        if text.startswith("--", i):
            end = re.search(r"\r?\n", text[i + 2 :])
            end = len(text) if end is None else i + 2 + end.start()
            ranges.append((i, end))
            i = end
            continue
        if text[i] in "'\"":
            quote, start = text[i], i
            i += 1
            while i < len(text):
                if text[i] == quote:
                    if text[i + 1 : i + 2] == quote:
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            ranges.append((start, i))
            continue
        i += 1
    return ranges


def _inside(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in ranges)


_IDENT = "[A-Za-z_$0-9.]+"


def _operand_back(text: str, i: int) -> tuple[int, int] | None:
    """Rango `[inicio, fin)` del operando que termina justo antes de `i` (incluye espacios al final no)."""
    j = i - 1
    while j >= 0 and text[j].isspace():
        j -= 1
    if j < 0:
        return None
    if text[j] == ")":
        depth = 0
        for k in range(j, -1, -1):
            if text[k] == ")":
                depth += 1
            elif text[k] == "(":
                depth -= 1
                if depth == 0:
                    f = k - 1
                    while f >= 0 and (text[f].isalnum() or text[f] in "_$."):
                        f -= 1
                    return f + 1, j + 1
        return None
    if text[j] in "'\"":
        quote, k = text[j], j - 1
        while k >= 0:
            if text[k] == quote:
                if text[k - 1 : k] == quote:  # '' escapada
                    k -= 2
                    continue
                return k, j + 1
            k -= 1
        return None
    m = re.search(_IDENT + r"$", text[: j + 1])
    return (m.start(), j + 1) if m else None


def _operand_forward(text: str, i: int) -> tuple[int, int] | None:
    """Rango `[inicio, fin)` del operando que empieza en `i`."""
    j = i
    while j < len(text) and text[j].isspace():
        j += 1
    if j >= len(text):
        return None
    if text[j] == "(":
        depth = 0
        for k in range(j, len(text)):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    return j, k + 1
        return None
    if text[j] in "'\"":
        quote, k = text[j], j + 1
        while k < len(text):
            if text[k] == quote:
                if text[k + 1 : k + 2] == quote:  # '' escapada
                    k += 2
                    continue
                return j, k + 1
            k += 1
        return None
    m = re.match(_IDENT, text[j:])
    if not m:
        return None
    end = j + m.end()
    if text[end : end + 1] == "(":  # llamada a función: consumir sus paréntesis equilibrados
        depth = 0
        for k in range(end, len(text)):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    return j, k + 1
        return None
    return j, end


def _rewrite_contains(text: str, notes: list[str]) -> str:
    """`A [NOT] contains B` → `A [NOT] LIKE CONCAT('%', B, '%')`, con operandos de expresión completa."""
    ranges = _protected_ranges(text)
    edits: list[tuple[int, int, str]] = []
    for match in _CONTAINS_WORD.finditer(text):
        if _inside(match.start(), ranges):
            continue
        not_match = re.search(r"(?i)\bnot$", text[: match.start()].rstrip())
        prefix, stop = ("NOT ", not_match.start()) if not_match else ("", match.start())
        lhs = _operand_back(text, stop)
        rhs = _operand_forward(text, match.end())
        if lhs is None or rhs is None:
            continue  # operando no reconocible: se deja para que salte PARSE_ERROR, no se adivina
        a = text[lhs[0] : lhs[1]].strip()
        b = text[rhs[0] : rhs[1]]
        like = "NOT LIKE" if prefix else "LIKE"
        edits.append((lhs[0], rhs[1], f"{prefix}{a} {like} CONCAT('%', {b}, '%')"))
    if not edits:
        return text
    out, last = [], 0
    for start, end, repl in sorted(edits, key=lambda e: e[0]):
        if start < last:  # solapamiento: se deja el original
            continue
        out.append(text[last:start])
        out.append(repl)
        last = end
    out.append(text[last:])
    notes.append("contains reescrito a LIKE CONCAT(...)")
    return "".join(out)


def _proteger_funciones_por_fila(text: str, marcadores: dict[str, str]) -> str:
    """Evita que sqlglot lea las funciones SAS multiargumento como agregados de un argumento."""
    protegidos = _protected_ranges(text)
    ediciones = []
    for match in _MULTIARG_ROW_FUNCTION.finditer(text):
        if _inside(match.start(), protegidos):
            continue
        apertura = match.end()
        while True:
            while apertura < len(text) and text[apertura].isspace():
                apertura += 1
            comentario = next(
                (
                    fin
                    for inicio, fin in protegidos
                    if inicio == apertura and text.startswith(("/*", "--"), apertura)
                ),
                None,
            )
            if comentario is None:
                break
            apertura = comentario
        if apertura >= len(text) or text[apertura] != "(":
            continue

        profundidad = 0
        comas = 0
        cierre = None
        for posicion in range(apertura, len(text)):
            if _inside(posicion, protegidos):
                continue
            caracter = text[posicion]
            if caracter == "(":
                profundidad += 1
            elif caracter == ")":
                profundidad -= 1
                if profundidad == 0:
                    cierre = posicion
                    break
            elif caracter == "," and profundidad == 1:
                comas += 1
        if cierre is not None and comas:
            nombre = match.group(1).lower()
            marcador = f"sgm_row_{nombre}"
            sufijo = 1
            while re.search(rf"(?i)\b{re.escape(marcador)}\b", text):
                marcador = f"sgm_row_{nombre}_{sufijo}"
                sufijo += 1
            marcadores[marcador] = nombre
            ediciones.append((match.start(1), match.end(1), marcador))

    for inicio, fin, sustituto in reversed(ediciones):
        text = text[:inicio] + sustituto + text[fin:]
    return text


def normalize(sql: str) -> NormalizedSql:
    """SQL de PROC SQL en forma estándar, con lo que se quitó anotado."""
    result = NormalizedSql(text=sql)
    text = sql

    for match in _INTO.finditer(text):
        separator = match.group(2)
        for name in _INTO_NAME.findall(match.group(1)):
            result.into_vars.append((name, separator))
    if result.into_vars:
        text = _INTO.sub("", text)
        result.notes.append("INTO: variables de macro recibidas por el SELECT")

    text = _strip_options(text, result.notes)
    # Literal de fecha de SAS (`"01jan2024"d`): se queda como texto; el formato no se traduce.
    text = re.sub(r"(?i)(\"[^\"]*\"|'[^']*')d\b", r"\1", text)
    # Formatos e informatos de columnas en el SELECT (`format=dollar18.2`): solo presentación.
    text = re.sub(r"(?i)\b(?:format|informat)\s*=\s*[\w.$]+", "", text)
    if _LABEL.search(text):
        text = _LABEL.sub("", text)
        result.notes.append("LABEL=... retirado (solo presentación)")
    # En SAS, las comillas dobles son literales de texto (no identificadores).
    text = re.sub(r"\"([^\"']*)\"", r"'\1'", text)

    def name_literal(match: re.Match) -> str:
        inner = match.group(1).replace("''", "'")  # SAS escapa la comilla duplicándola
        return '"' + inner.replace('"', '""') + '"'

    if _NAME_LITERAL.search(text):
        text = _NAME_LITERAL.sub(name_literal, text)
        result.notes.append("name literals de SAS convertidos a identificador entre comillas dobles")

    def macro_ref(match: re.Match) -> str:
        placeholder = f"mv_{match.group(1)}"
        result.macros[placeholder] = f"&{match.group(1)}"
        return placeholder

    text = _MACRO_REF.sub(macro_ref, text)
    text = _MACRO_FN.sub(lambda m: f"fn_{m.group(1)}(", text)
    text = _CALCULATED.sub(lambda m: m.group(1), text)
    text = _rewrite_contains(text, result.notes)

    def operators(part: str) -> str:
        for word, symbol in _COMPARATORS.items():
            part = re.sub(rf"(?i)\b{word}\b", symbol, part)
        part = _NOT_EQ.sub("<>", part)
        part = part.replace("^=", "<>")
        part = re.sub(r"(?i)\bis\s+not\s+missing\b", "IS NOT NULL", part)
        part = re.sub(r"(?i)\bis\s+missing\b", "IS NULL", part)
        part = _MISSING_LITERAL.sub(lambda m: " IS NOT NULL" if m.group(1) == "<>" else " IS NULL", part)
        return part

    text = _outside_quotes(text, operators)

    informat_seen = False

    def informat_args(part: str) -> str:
        nonlocal informat_seen
        new_part = _INFORMAT_ARG.sub(lambda m: f"{m.group(1)}'{m.group(2)}'{m.group(3)}", part)
        informat_seen = informat_seen or new_part != part
        return new_part

    text = _outside_quotes(text, informat_args)
    if informat_seen:
        result.notes.append("informatos de SAS pasados a texto (no se traducen)")
    text = _FORMAT_ARG.sub(lambda m: f"{m.group(1)}'{m.group(2)}'{m.group(3)}", text)
    text = _proteger_funciones_por_fila(text, result.row_functions)
    if result.macros:
        result.notes.append("referencias de macro sustituidas por identificadores")
    result.text = text.strip()
    return result
