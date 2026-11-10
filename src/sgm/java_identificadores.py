"""Validación conservadora de identificadores que se interpolan en código Java."""

from __future__ import annotations

import re

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_RESERVED = frozenset(
    """
    abstract assert boolean break byte case catch char class const continue default do double else
    enum extends final finally float for goto if implements import instanceof int interface long
    native new package private protected public return short static strictfp super switch
    synchronized this throw throws transient try void volatile while true false null _ var yield
    record sealed permits when module open opens requires transitive exports to uses provides with
    """.split()
)


def is_java_identifier(value: str) -> bool:
    """Indica si el nombre es un identificador ASCII portable y no reservado en Java."""
    return isinstance(value, str) and bool(_IDENTIFIER.fullmatch(value)) and value not in _RESERVED


def require_context_identifier(value: str) -> str:
    """Valida el nombre de contexto sin repetirlo en el error ni tratarlo como código."""
    if not is_java_identifier(value):
        raise ValueError("identificador de contexto inválido")
    return value


def require_column_identifier(value: str) -> str:
    """Valida un campo que el emisor interpola como acceso Java."""
    if not is_java_identifier(value):
        raise ValueError("identificador de columna no portable para Java")
    return value


__all__ = [
    "is_java_identifier",
    "require_column_identifier",
    "require_context_identifier",
]
