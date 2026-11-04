"""Arquitectura de Jobs declarada por el equipo: nombres de los Jobs, entornos y proyecto.

Vive en `decisiones/<programa>.jobs.yaml`. El SAS no dice cuántos Jobs hay ni cómo se llaman: es una
decisión de diseño, igual que las etapas. Los productos no se declaran aquí: salen de la agrupación.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

JOBS_REQUERIDOS = ("padre", "insumos", "producto", "totales", "conciliacion")


@dataclass(frozen=True)
class Arquitectura:
    proyecto: str
    entornos: tuple[str, ...]
    padre: str
    insumos: str
    producto: str
    totales: str
    conciliacion: str
    mensaje_fin: str


def cargar_arquitectura(path: Path) -> Arquitectura:
    """Lee la arquitectura. Un archivo mal formado falla con su nombre y el motivo."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    proyecto = str(data.get("proyecto") or "").strip()
    if not proyecto:
        raise ValueError(f"{path}: falta proyecto")
    jobs = data.get("jobs") or {}
    faltan = [k for k in JOBS_REQUERIDOS if not str(jobs.get(k) or "").strip()]
    if faltan:
        raise ValueError(f"{path}: faltan los Jobs {faltan}")
    entornos = tuple(str(e).strip() for e in (data.get("entornos") or []) if str(e).strip())
    if not entornos:
        raise ValueError(f"{path}: falta entornos")
    return Arquitectura(
        proyecto,
        entornos,
        *(str(jobs[k]).strip() for k in JOBS_REQUERIDOS),
        mensaje_fin=str(data.get("mensaje_fin") or "").strip(),
    )
