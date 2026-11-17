"""Lectura de YAML del proyecto: un solo cargador, con el lector C cuando está disponible.

`yaml.safe_load` usa el analizador escrito en Python puro. `CSafeLoader` (libyaml) interpreta el
mismo YAML con el mismo conjunto de tipos y entre cinco y diez veces más rápido. La suite carga
miles de documentos al recolectar, así que la diferencia se nota en cada corrida.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

#: Cargador seguro para todo el proyecto. `CSafeLoader` solo existe si PyYAML se instaló con
#: libyaml; si no, se usa el de Python puro y el resultado es el mismo.
CARGADOR = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def cargar_texto(texto: str) -> Any:
    """Interpreta un documento YAML con el mismo conjunto de tipos que `safe_load`."""
    return yaml.load(texto, Loader=CARGADOR)


def cargar_yaml(ruta: Path | str) -> Any:
    """Lee un archivo YAML en UTF-8 y lo interpreta."""
    return cargar_texto(Path(ruta).read_text(encoding="utf-8"))
