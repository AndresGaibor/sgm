"""Carga de la referencia manual (YAML): secciones y filas, en el orden del documento."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from sgm.compile import ROOT_DIR

REFERENCIA = ROOT_DIR / "tests" / "fixtures" / "referencia" / "diseno_manual.yaml"
CLASIFICACIONES = ("derivable", "declarada", "humana")


@dataclass(frozen=True)
class Fila:
    """Una fila de la referencia, ya ligada a su sección."""

    seccion: str
    id: str
    clave: str
    clasificacion: str
    motivo: str
    campos: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Seccion:
    codigo: str
    titulo: str
    md: bool | str  # True: tabla Markdown; "lista": viñetas o numerada; False: nota suelta
    columnas: list[str]
    filas: list[Fila]


def cargar_secciones(ruta: Path = REFERENCIA) -> dict[str, Seccion]:
    """Lee el YAML y devuelve las secciones en el orden del documento."""
    crudo = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    secciones: dict[str, Seccion] = {}
    for codigo, datos in crudo["secciones"].items():
        codigo = str(codigo)
        filas = [
            Fila(
                seccion=codigo,
                id=str(f["id"]),
                clave=str(f["clave"]),
                clasificacion=f["clasificacion"],
                motivo=f["motivo"],
                campos={k: str(v) for k, v in (f.get("campos") or {}).items()},
            )
            for f in datos["filas"]
        ]
        secciones[codigo] = Seccion(
            codigo=codigo,
            titulo=datos["titulo"],
            md=datos.get("md", True),
            columnas=list(datos.get("columnas") or []),
            filas=filas,
        )
    return secciones


def todas_las_filas(secciones: dict[str, Seccion]) -> list[Fila]:
    return [fila for s in secciones.values() for fila in s.filas]
