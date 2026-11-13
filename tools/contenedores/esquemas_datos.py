"""Lectura explícita de esquemas para generar datos sintéticos."""

import json
from pathlib import Path

from sgm.catalog.schemas import load_schemas
from sgm.ir.models import Column


def cargar_esquemas_datos(carpeta: Path) -> dict[str, list[Column]]:
    """Lee catálogos y propuestas inferidas, conservando el origen de estas últimas."""
    if not carpeta.is_dir():
        raise ValueError(f"no existe la carpeta de esquemas: {carpeta}")
    schemas = load_schemas(carpeta)
    for ruta in sorted(carpeta.glob("*.json")):
        if ruta.name.startswith("_"):
            continue
        raw = json.loads(ruta.read_text(encoding="utf-8"))
        for tabla, columnas in raw.get("tables", {}).items():
            if tabla.startswith("_"):
                continue
            key = f"{ruta.stem.lower()}.{tabla.lower()}"
            if raw.get("_inferido") is True:
                schemas[key] = [
                    Column(
                        str(c["name"]),
                        c.get("type"),
                        c.get("length"),
                        str(c.get("source") or "unknown"),
                    )
                    for c in columnas
                ]
            elif key in schemas:
                for columna, original in zip(schemas[key], columnas, strict=True):
                    if original.get("type") is not None and columna.type is None:
                        columna.type = original["type"]
    return schemas
