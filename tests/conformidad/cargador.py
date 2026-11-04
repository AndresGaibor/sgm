"""Carga de la referencia manual (YAML) y lectura del documento Markdown de origen."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
REFERENCIA = RAIZ / "tests" / "fixtures" / "referencia" / "diseno_manual.yaml"
DOCUMENTO = RAIZ / "docs" / "diseno-talend-exogena-depositos.md"
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


_ENCABEZADO = re.compile(r"^#{2,3}\s+(\d+(?:\.\d+)?)\.?\s")


def contar_filas_documento(ruta: Path = DOCUMENTO) -> dict[str, dict[str, int]]:
    """Cuenta, por código de sección del Markdown, filas de tabla y elementos de lista.

    Devuelve `{codigo: {"tabla": n, "lista": m}}`. La fila de encabezado y la línea separadora
    de cada tabla no cuentan.
    """
    cuentas: dict[str, dict[str, int]] = {}
    actual: str | None = None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        coincide = _ENCABEZADO.match(linea)
        if coincide:
            actual = coincide.group(1)
            cuentas[actual] = {"tabla": 0, "lista": 0}
            continue
        if actual is None:
            continue
        if linea.startswith("|"):
            cuentas[actual]["tabla"] += 1
        elif linea.startswith("- ") or re.match(r"^\d+\.\s", linea):
            cuentas[actual]["lista"] += 1
    for conteo in cuentas.values():
        if conteo["tabla"]:
            conteo["tabla"] -= 2  # encabezado y separador
    return cuentas
