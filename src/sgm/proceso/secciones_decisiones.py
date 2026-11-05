"""Sección 5 del diseño: decisiones abiertas o tomadas, desde su YAML en `decisiones/`.

El emisor no deduce nada del SAS: copia cada decisión del YAML, valida que traiga id, texto,
motivo, estado y valor por omisión, y que el estado sea `abierta` o `tomada`. Es contenido del
equipo, así que la sección no entra en la conformidad fila a fila.
"""

from __future__ import annotations

from pathlib import Path

import yaml

Fila = dict[str, str]
Seccion = dict[str, Fila]

ESTADOS = ("abierta", "tomada")
CAMPOS = ("texto", "motivo", "estado", "valor_por_omision")
ETIQUETAS = {
    "texto": "texto",
    "motivo": "motivo",
    "estado": "estado",
    "valor_por_omision": "valor por omisión",
}


def cargar_decisiones(path: Path) -> list[dict[str, str]]:
    """Decisiones del YAML, en su orden. Sin archivo, la lista está vacía."""
    if not path.is_file():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    decisiones: list[dict[str, str]] = []
    vistas: set[str] = set()
    for item in data.get("decisiones") or []:
        item = {str(k): str(v).strip() for k, v in (item or {}).items()}
        identificador = item.get("id", "")
        if not identificador:
            raise ValueError(f"{path}: cada decisión necesita `id`")
        if identificador in vistas:
            raise ValueError(f"{path}: repite el id {identificador!r}")
        vistas.add(identificador)
        for campo in CAMPOS:
            if not item.get(campo):
                raise ValueError(f"{path}: {identificador!r} necesita `{campo}`")
        if item["estado"] not in ESTADOS:
            raise ValueError(f"{path}: {identificador!r} tiene estado {item['estado']!r}")
        decisiones.append(item)
    return decisiones


def seccion_decisiones(decisiones: list[dict[str, str]]) -> Seccion:
    """Sección 5: una fila por decisión, con sus campos en español."""
    return {
        d["id"]: {ETIQUETAS[campo]: d[campo] for campo in CAMPOS} for d in decisiones
    }
