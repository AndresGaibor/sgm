"""Modelos de la importación: tipo de archivo, archivo aceptado y archivo omitido."""

from dataclasses import dataclass
from enum import StrEnum


class FileKind(StrEnum):
    SAS = "sas"
    SHELL = "shell"
    LOG = "log"
    DOC = "doc"
    OTHER = "other"


@dataclass(frozen=True)
class SourceFile:
    path: str  # relativa, separador "/"
    sha256: str
    size: int
    kind: FileKind
    encoding: str | None = None  # None si no es texto


@dataclass(frozen=True)
class Skipped:
    path: str
    reason: str
