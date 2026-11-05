"""Arquitectura de Jobs declarada por el equipo: nombres de los Jobs, entornos y proyecto.

Vive en `decisiones/<programa>.jobs.yaml`. El SAS no dice cuántos Jobs hay ni cómo se llaman: es una
decisión de diseño, igual que las etapas. Los productos no se declaran aquí: salen de la agrupación.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

JOBS_REQUERIDOS = ("padre", "producto", "totales", "conciliacion")


@dataclass(frozen=True)
class PeriodoDecl:
    """El Excel de la fecha del proceso: el padre lo lee una vez y deja su valor en el contexto."""

    fuente: str  # clave de la tabla 1.1 del diseño
    variables: tuple[tuple[str, str], ...]  # (columna del Excel, variable de contexto)


@dataclass(frozen=True)
class Arquitectura:
    proyecto: str
    entornos: tuple[str, ...]
    padre: str
    producto: str
    totales: str
    conciliacion: str
    mensaje_fin: str
    periodo: PeriodoDecl | None = None
    lookups: tuple[str, ...] = ()  # fuentes Excel que job_producto usa como lookup
    columna_saldo: str = ""  # columna cuya suma son los totales de origen (el SAS la suma)


def _periodo(path: Path, item: dict | None) -> PeriodoDecl | None:
    if not item:
        return None
    fuente = str(item.get("fuente") or "").strip()
    variables = tuple((str(c), str(v)) for c, v in (item.get("variables") or {}).items())
    if not fuente or not variables:
        raise ValueError(f"{path}: `periodo` necesita fuente y variables")
    return PeriodoDecl(fuente, variables)


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
        periodo=_periodo(path, data.get("periodo")),
        lookups=tuple(str(x).strip() for x in (data.get("lookups_producto") or [])),
        columna_saldo=str((data.get("total_origen") or {}).get("columna_saldo") or "").strip(),
    )
