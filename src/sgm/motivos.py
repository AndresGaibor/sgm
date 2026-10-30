"""Registro de motivos de hueco: cada motivo tiene dueño, arreglo y se sabe si está en el contrato.

Los motivos viven en `rules/routing.yaml` (F1.5): añadir o reasignar uno es editar ese archivo.
Los motivos de la lista del contrato (`docs/plan-sgm-v2/05-contratos.md`, sección 3) son los que
el equipo acordó. Los que están en `contrato_pendiente` no lo están hasta que los tres los acepten:
cambiar la lista es un cambio de contrato.

Los motivos `no_hueco` no son huecos: son estados que el código registra en `not_migrated`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROUTING = ROOT / "rules" / "routing.yaml"


@dataclass(frozen=True)
class Motivo:
    codigo: str
    dueño: str  # joseph, byron o andres (ver docs/plan-sgm-v2/01-reparto.md)
    contrato: bool  # está en la lista cerrada del contrato
    se_cierra_con: str
    tipo_regla: str | None = None  # tipo que sugiere `sgm rules new`, si hay uno


def _cargar(path: Path = ROUTING) -> tuple[Motivo, ...]:
    """Motivos de `routing.yaml`, en el orden del archivo."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    pendientes = set(data.get("contrato_pendiente", []))
    fix_with = data.get("fix_with", {})
    tipos = data.get("tipo_regla", {})
    return tuple(
        Motivo(
            codigo=codigo,
            dueño=dueño,
            contrato=codigo not in pendientes,
            se_cierra_con=fix_with.get(codigo, ""),
            tipo_regla=tipos.get(codigo),
        )
        for codigo, dueño in data["owners"].items()
    )


HUECOS: tuple[Motivo, ...] = _cargar()

NO_HUECO: tuple[str, ...] = (
    "CONFIGURACION",  # sesión o macro: lo resuelve el contexto del Job
    "CONEXION_SQL",  # conexión a un motor: fontanería
    "INCLUDE_DECLARADO",  # %include declarado: contexto y no migrado
    "REPORTE",  # reporte impreso: lo decide la política `reports`
)

_POR_CODIGO = {m.codigo: m for m in HUECOS}


def de(codigo: str) -> Motivo | None:
    """Motivo registrado, o None si el código no está en el registro."""
    return _POR_CODIGO.get(codigo)


def sin_registrar(codigos: set[str]) -> set[str]:
    """Motivos usados que no están en el registro de huecos ni en la lista de no-huecos."""
    return {c for c in codigos if c not in _POR_CODIGO and c not in NO_HUECO}
