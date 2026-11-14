"""Comprobaciones estáticas de biblioteca SAS para no borrar datos persistentes."""

from __future__ import annotations

import re

_PROC_DELETE = re.compile(r"(?i)^\s*proc\s+delete\b")
_DATA_OPTION = re.compile(r"(?i)\bdata\s*=\s*")
_LIBRARY_OPTION = re.compile(r"(?i)\b(?:library|lib)\s*=\s*(['\"]?)([^'\"\s;]+)")
_EXPLICIT_LIBREF = re.compile(r"(?i)(?<![\w])([a-z_&%][\w&%.]*)\s*\.")
_LITERAL_LIBREF = re.compile(r"(?i)(?<![&%.\w])([a-z_][a-z0-9_]*)\s*\.")


def is_work_library(library: str | None) -> bool:
    """Devuelve True solo para una biblioteca literal WORK."""
    return bool(library and library.strip("'\"").casefold() == "work")


def is_work_dataset(dataset: str | None, *, default_work: bool = True) -> bool:
    """Comprueba WORK por libref explícito o por el default indicado por el llamador."""
    if not dataset:
        return False
    name = dataset.strip().rstrip(";")
    if "." not in name:
        return default_work
    library = name.split(".", 1)[0].strip()
    return is_work_library(library)


def explicit_dataset_libraries(dataset: str | None) -> tuple[str, ...]:
    """Nombres de libref literales, excluyendo referencias macro y tokens dinámicos."""
    if not dataset:
        return ()
    return tuple(match.upper() for match in _LITERAL_LIBREF.findall(dataset))


def is_work_delete(statement: str) -> bool:
    """Confirma que PROC DELETE solo alcanza miembros de WORK (p. 839 y 847)."""
    if not _PROC_DELETE.match(statement):
        return False
    header = statement.split(";", 1)[0]
    libraries = [value for _, value in _LIBRARY_OPTION.findall(header)]
    if any(not is_work_library(value) for value in libraries):
        return False
    data = _DATA_OPTION.search(header)
    if data is None:
        return False
    members = _LIBRARY_OPTION.sub(" ", header[data.end() :])
    members = re.sub(r"\([^()]*\)", " ", members)
    tokens = [token.strip(",") for token in members.split() if token.strip(",")]
    if not tokens or any("=" in token for token in tokens):
        return False
    explicit_libraries = [
        library for token in tokens for library in _EXPLICIT_LIBREF.findall(token)
    ]
    return all(is_work_library(library) for library in explicit_libraries)
