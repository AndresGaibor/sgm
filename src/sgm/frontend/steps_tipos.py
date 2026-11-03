"""Tipos de los pasos de un nodo (sin lógica): cada paso es un dataclass con su línea y su texto."""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.frontend.sql import SqlStatement


@dataclass
class ProcSql:
    statements: list[SqlStatement]
    line: int
    end_line: int
    text: str


@dataclass
class Proc:
    name: str
    options: dict[str, str]  # DATA=, OUT=, etc., con clave en minúsculas
    flags: list[str]  # opciones sin valor (nodupkey, noprint...)
    clauses: dict[str, str]  # BY, VAR, CLASS, WHERE, ... con el texto de la sentencia
    line: int
    end_line: int
    text: str
    body: list[str] = field(default_factory=list)  # todas las sentencias del cuerpo, tal cual


@dataclass
class MacroDef:
    name: str
    params: list[str]
    body: list[object]
    line: int
    end_line: int
    text: str


@dataclass
class MacroCall:
    name: str
    args: str
    line: int
    end_line: int
    text: str


@dataclass
class Let:
    name: str
    value: str
    line: int
    end_line: int
    text: str


@dataclass
class Include:
    path: str | None
    line: int
    end_line: int
    text: str


@dataclass
class Libname:
    name: str
    value: str
    line: int
    end_line: int
    text: str


@dataclass
class Options:
    text: str
    line: int
    end_line: int


@dataclass
class XCommand:
    command: str
    line: int
    end_line: int
    text: str


@dataclass
class Global:
    text: str
    line: int
    end_line: int


@dataclass
class Unparsed:
    text: str
    reason: str
    line: int
    end_line: int


@dataclass
class ParsedNode:
    label: str | None
    line_start: int
    line_end: int
    steps: list[object] = field(default_factory=list)
