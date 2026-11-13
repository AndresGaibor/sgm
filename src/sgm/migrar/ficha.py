"""Ficha de procedencia y tipos declarados de un fixture."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Ficha:
    """Origen y tipos declarados por el fixture; no se infieren de los valores."""

    tabla: str
    origen: str
    filas: int
    columnas: dict[str, str]
    semilla: int | None = None
    generador: str | None = None
    procedencia: str | None = None
    nota: str = ""


def leer_ficha(ruta: Path) -> Ficha:
    """Lee una ficha YAML conservando el orden declarado de las columnas."""
    return Ficha(**yaml.safe_load(ruta.read_text(encoding="utf-8")))


def validar_procedencia(ficha: Ficha) -> list[str]:
    """Valida origen y procedencia sin inspeccionar las filas del archivo."""
    errors = []
    if ficha.origen not in {"sintetico", "real"}:
        errors.append(f"origen no permitido: {ficha.origen}")
    if ficha.origen == "sintetico":
        if ficha.semilla is None:
            errors.append("origen sintetico sin semilla")
        if not ficha.generador:
            errors.append("origen sintetico sin generador")
    if ficha.origen == "real" and not ficha.procedencia:
        errors.append("origen real sin procedencia")
    return errors
