"""Esquemas de entorno desde `env/schemas.json`.

Formato: `{"<libreria>.<tabla>": [{"name": "...", "type": "String"}]}`. Las claves
se comparan en minúsculas. Un tipo fuera de los de Talend se conserva tal cual y se marca como
desconocido al compilar: nunca se inventa un tipo.
"""

from __future__ import annotations

import json
from pathlib import Path

from sgm.ir.models import Column

TALEND_TYPES = frozenset({"String", "Integer", "Long", "Double", "BigDecimal", "Date", "Boolean"})


def load_schemas(path: Path) -> dict[str, list[Column]]:
    """Esquemas del archivo, con la clave en minúsculas. Vacío si el archivo no existe."""
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    schemas: dict[str, list[Column]] = {}
    for key, columns in raw.items():
        if key.startswith("_"):
            continue
        schemas[key.lower()] = [
            Column(
                name=str(c["name"]).lower(),
                type=c.get("type") if c.get("type") in TALEND_TYPES else None,
                length=c.get("length"),
                source="catalog",
            )
            for c in columns
        ]
    return schemas
