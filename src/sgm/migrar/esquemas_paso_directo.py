"""Esquemas locales de las tablas que usa SQL pass-through."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import sqlglot
from sqlglot import exp

from sgm.ir.models import Column, Plan

_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _fuentes(op) -> list[str]:
    sql = str(op.params.get("sql") or "")
    engine = str(op.params.get("engine") or "").lower()
    dialecto = {"impala": "hive", "postgres": "postgres"}.get(engine)
    if dialecto is None:
        return []
    try:
        consulta = sqlglot.parse_one(sql, read=dialecto)
    except sqlglot.errors.SqlglotError:
        return []
    if not isinstance(consulta, exp.Select):
        return []

    nombres: dict[str, None] = {}
    for tabla in consulta.find_all(exp.Table):
        partes = [str(parte) for parte in (tabla.catalog, tabla.db, tabla.name) if parte]
        if not partes or any(not _IDENTIFICADOR.fullmatch(parte) for parte in partes):
            return []
        nombres[".".join(partes).lower()] = None
    return list(nombres)


def _desde_muestra(muestra: Path | None, tabla: str) -> list[Column]:
    if muestra is None or not muestra.is_dir():
        return []
    ruta = muestra / f"{tabla}.csv"
    if not ruta.is_file():
        return []
    try:
        with ruta.open(encoding="utf-8-sig", newline="") as archivo:
            nombres = next(csv.reader(archivo), [])
    except (OSError, csv.Error, UnicodeError):
        return []
    if not nombres or len({nombre.casefold() for nombre in nombres}) != len(nombres):
        return []
    if any(not _IDENTIFICADOR.fullmatch(nombre) for nombre in nombres):
        return []
    return [Column(nombre, None, source="file_header") for nombre in nombres]


def esquemas_paso_directo(
    plan: Plan, catalogo: dict[str, list[Column]], muestra: Path | None = None
) -> dict[str, list[Column]]:
    """Conserva solo esquemas demostrados para las fuentes en lecturas directas de base."""
    esquemas: dict[str, list[Column]] = {}
    indice = {nombre.casefold(): columnas for nombre, columnas in catalogo.items()}
    for op in plan.graph.operators():
        if op.kind != "read" or not (op.placement or "").startswith("db:"):
            continue
        for fuente in _fuentes(op):
            columnas = indice.get(fuente)
            if columnas is None and "." not in fuente:
                columnas = indice.get(fuente)
            if columnas is None:
                columnas = _desde_muestra(muestra, fuente)
            if columnas:
                esquemas[fuente] = [
                    Column(c.name, c.type, c.length, c.source) for c in columnas
                ]
    return esquemas


__all__ = ["esquemas_paso_directo"]
