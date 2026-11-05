"""Carpeta de trabajo de una ejecución en Studio: copia de las entradas y carpeta de salida.

Estructura: `<trabajo>/entradas/` (copia de `entradas/`), `<trabajo>/entradas_preparadas/` si el
caso la tiene, y `<trabajo>/salida/`, donde el Job escribe. La copia evita que un Job modifique
las entradas del repositorio.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .caso import Caso


def preparar_trabajo(caso: Caso, trabajo: Path) -> Path:
    """Copia las entradas del caso a `trabajo` y crea `salida/` vacía."""
    trabajo.mkdir(parents=True, exist_ok=True)
    for origen, nombre in ((caso.entradas, "entradas"), (caso.entradas_preparadas, None)):
        if origen.is_dir():
            destino = trabajo / (nombre or origen.name)
            shutil.copytree(origen, destino, dirs_exist_ok=True)
    (trabajo / "salida").mkdir(exist_ok=True)
    return trabajo


def archivos_salida(trabajo: Path) -> list[Path]:
    """Archivos `.csv` que el Job dejó en `salida/`, en orden por nombre."""
    carpeta = trabajo / "salida"
    if not carpeta.is_dir():
        return []
    return sorted(p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() == ".csv")
