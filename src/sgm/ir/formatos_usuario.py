"""Contrato de formatos discretos de usuario para el plan D1."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatoUsuario:
    nombre: str
    rangos: tuple[tuple[str, str], ...]
    otro: str | None = None
