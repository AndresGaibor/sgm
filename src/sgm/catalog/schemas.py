"""Esquemas de entorno desde `env/schemas/` (F1.9).

Una carpeta de archivos `<esquema>.json`, uno por base. Cada archivo lleva sus tablas:

    {"schema": "ejemplo_lz", "tables": {"clientes": [{"name": "cliente_id", "type": "Integer"}]}}

El cargador devuelve claves `<esquema>.<tabla>` en minúsculas. Un tipo fuera de los de Talend se
conserva tal cual y se marca como desconocido al compilar: nunca se inventa un tipo.
Los archivos generados con `sgm env import-describe` tienen la misma forma.
"""

from __future__ import annotations

import json
from pathlib import Path

from sgm.ir.models import Column

TALEND_TYPES = frozenset({"String", "Integer", "Long", "Double", "BigDecimal", "Date", "Boolean"})


def _columnas(items: list[dict]) -> list[Column]:
    return [
        Column(
            name=str(c["name"]).lower(),
            type=c.get("type") if c.get("type") in TALEND_TYPES else None,
            length=c.get("length"),
            source="catalog",
        )
        for c in items
    ]


def load_schemas(directory: Path) -> dict[str, list[Column]]:
    """Esquemas de todos los `<esquema>.json` de la carpeta. Vacío si la carpeta no existe.

    Las claves y los nombres de tabla que empiezan por `_` son notas y se ignoran.
    """
    if not directory.is_dir():
        return {}
    schemas: dict[str, list[Column]] = {}
    for path in sorted(directory.glob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        esquema = path.stem.lower()
        for tabla, items in raw.get("tables", {}).items():
            if not tabla.startswith("_"):
                schemas[f"{esquema}.{tabla.lower()}"] = _columnas(items)
    return schemas
