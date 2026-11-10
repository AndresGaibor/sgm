"""Firma de un operador: huella de su tipo y de sus parámetros normalizados.

Se normalizan nombres de tablas y columnas, literales, números y macro variables. Se conservan las
palabras clave, los operadores y los nombres de función (lo que sigue a `(`). Así dos pasos que solo
cambian nombres dan la misma firma. La firma es la llave de overrides, huecos, plantillas y caché.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

#: Palabras que describen la lógica y se conservan tal cual.
KEYWORDS = frozenset(
    {
        "and",
        "or",
        "not",
        "if",
        "then",
        "else",
        "is",
        "null",
        "missing",
        "in",
        "between",
        "like",
        "as",
        "select",
        "from",
        "where",
        "group",
        "by",
        "order",
        "having",
        "case",
        "when",
        "end",
        "distinct",
        "join",
        "left",
        "right",
        "full",
        "inner",
        "outer",
        "on",
        "union",
        "all",
        "eq",
        "ne",
        "lt",
        "gt",
        "le",
        "ge",
        "first",
        "last",
        "output",
        "keep",
        "drop",
        "rename",
        "retain",
        "set",
        "merge",
        "do",
        "to",
        "create",
        "table",
        "insert",
        "delete",
        "into",
        "values",
        "with",
        "true",
        "false",
        "desc",
        "asc",
        "limit",
        "over",
        "partition",
        "row_number",
    }
)
_TOKEN = re.compile(
    r"""('(?:[^']|'')*'|"(?:[^"]|"")*")"""  # literales de texto
    r"""|(&[A-Za-z_]\w*\.?)"""  # macro variables
    r"""|(\b\d+(?:\.\d+)?\b)"""  # números
    r"""|([A-Za-z_][\w.]*)(\s*\()?"""  # identificadores (y función si sigue `(`)
    r"""|(\S)"""  # resto: operadores y signos
)


def normalize_text(text: str) -> str:
    """Texto con literales, números, macro variables e identificadores (no clave) sustituidos."""

    def rep(m: re.Match[str]) -> str:
        literal, macro, number, ident, call, other = m.groups()
        if literal:
            return "'S'"
        if macro:
            return "M"
        if number:
            return "N"
        if ident:
            low = ident.lower()
            if call or low in KEYWORDS:
                return low + (call or "")
            return "I"
        return other or ""

    return " ".join(_TOKEN.sub(rep, text).split())


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, dict):
        return {
            str(k).lower(): _normalize(v)
            for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))
            if str(k).lower() != "interpreter_subquery"
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return value


def signature(kind: str, params: dict[str, Any]) -> str:
    """Firma estable de 16 caracteres: tipo de operador más parámetros normalizados."""
    canonical = json.dumps(
        {"kind": kind, "params": _normalize(params)}, sort_keys=True, ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
