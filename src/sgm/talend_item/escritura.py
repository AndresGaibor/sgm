"""Escritura de un Job en disco: el par `.item` y `.properties` que Studio guarda en `process/`."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sgm.talend_item.item import render_item, render_properties
from sgm.talend_item.modelo import Job


def fecha_studio(ahora: datetime | None = None) -> str:
    """Fecha en el formato que Studio guarda en `.properties`: `2026-11-04T16:30:00.000-0500`."""
    return (ahora or datetime.now().astimezone()).strftime("%Y-%m-%dT%H:%M:%S.000%z")


def escribir_job(job: Job, carpeta: Path, fecha: str | None = None) -> tuple[Path, Path]:
    """Escribe `<nombre>_<versión>.item` y `.properties` en `carpeta` y devuelve sus rutas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    base = f"{job.nombre}_{job.version}"
    item, propiedades = carpeta / f"{base}.item", carpeta / f"{base}.properties"
    item.write_text(render_item(job), encoding="utf-8", newline="\n")
    propiedades.write_text(
        render_properties(job, fecha=fecha or fecha_studio()), encoding="utf-8", newline="\n"
    )
    return item, propiedades
