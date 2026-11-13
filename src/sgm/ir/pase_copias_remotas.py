"""Resuelve transferencias SAS/CONNECT de archivos como alias de ruta."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from sgm.frontend.lexer import split_statements
from sgm.ir.models import Plan
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.desde_plan_nodos import ruta

_PROC = re.compile(r"^\s*proc\s+(upload|download)\b", re.IGNORECASE)
_OPCION = re.compile(
    r"""(?ix)\b([a-z_]\w*)\s*=\s*("(?:[^"]|"")*"|'(?:[^']|'')*'|[^\s;]+)"""
)
_OPCIONES_DATASET = frozenset({"data", "out", "inlib", "outlib", "incat", "outcat"})


@dataclass(frozen=True)
class CopiaRemota:
    """Transferencia literal entre una ruta del cliente y otra del servidor SAS/CONNECT."""

    sentido: str
    infile: str
    outfile: str
    linea: int


def _opciones(texto: str) -> dict[str, list[str]]:
    """Extrae opciones simples sin conservar las comillas de sus valores."""
    opciones: dict[str, list[str]] = {}
    for coincidencia in _OPCION.finditer(texto):
        nombre = coincidencia.group(1).casefold()
        valor = ruta(coincidencia.group(2))
        opciones.setdefault(nombre, []).append(valor)
    return opciones


def copias_remotas(texto: str) -> tuple[list[CopiaRemota], list[PendienteMigracion]]:
    """Lee procedimientos UPLOAD/DOWNLOAD de archivos y deja lo dinámico como pendiente."""
    copias: list[CopiaRemota] = []
    pendientes: list[PendienteMigracion] = []
    for sentencia in split_statements(texto):
        proc = _PROC.match(sentencia.text)
        if not proc:
            continue
        sentido = proc.group(1).casefold()
        opciones = _opciones(sentencia.text)
        if _OPCIONES_DATASET.intersection(opciones):
            pendientes.append(
                PendienteMigracion(
                    "P-COPIA-REMOTA-DATASET",
                    f"PROC {sentido.upper()} transfiere datasets o catálogos; solo se resuelven "
                    "archivos con INFILE= y OUTFILE=",
                    sentencia.line,
                )
            )
            continue

        infile = opciones.get("infile", [])
        outfile = opciones.get("outfile", [])
        if len(infile) != 1 or len(outfile) != 1 or not infile[0] or not outfile[0]:
            pendientes.append(
                PendienteMigracion(
                    "P-COPIA-REMOTA-INCOMPLETA",
                    f"PROC {sentido.upper()} requiere un INFILE= y un OUTFILE= literales",
                    sentencia.line,
                )
            )
            continue
        if "&" in infile[0] or "&" in outfile[0]:
            pendientes.append(
                PendienteMigracion(
                    "P-COPIA-REMOTA-DINAMICA",
                    f"PROC {sentido.upper()} usa una macrovariable en la ruta",
                    sentencia.line,
                )
            )
            continue
        copias.append(CopiaRemota(sentido, infile[0], outfile[0], sentencia.line))
    return copias, pendientes


def _clave_ruta(literal: str | None) -> str:
    """Compara rutas sin distinguir mayúsculas ni el separador usado."""
    return ruta(literal).replace("\\", "/").casefold()


def aplicar_copias(
    plan: Plan, copias: Sequence[CopiaRemota]
) -> tuple[Plan, list[PendienteMigracion]]:
    """Redirige lecturas/escrituras que apuntaban a la ruta intermedia local."""
    pendientes: list[PendienteMigracion] = []
    for copia in copias:
        esperada = copia.outfile if copia.sentido == "download" else copia.infile
        campo = "datafile" if copia.sentido == "download" else "outfile"
        tipo = "read_file" if copia.sentido == "download" else "write_file"
        reemplazo = copia.infile if copia.sentido == "download" else copia.outfile
        encontrados = 0
        for op in plan.graph.operators():
            if op.kind != tipo or _clave_ruta(str(op.params.get(campo) or "")) != _clave_ruta(
                esperada
            ):
                continue
            op.params[campo] = reemplazo
            encontrados += 1
        if not encontrados:
            pendientes.append(
                PendienteMigracion(
                    "P-COPIA-REMOTA-SIN-EFECTO",
                    f"PROC {copia.sentido.upper()} no coincide con una operación {tipo} del plan",
                    copia.linea,
                )
            )
    return plan, pendientes


__all__ = ["CopiaRemota", "aplicar_copias", "copias_remotas"]
