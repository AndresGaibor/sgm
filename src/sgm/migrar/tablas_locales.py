"""Carga de tablas locales descritas por fichas de procedencia."""

from __future__ import annotations

import csv as csv_module
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from sgm.catalog.schemas import TALEND_TYPES
from sgm.ir.models import Column
from sgm.migrar.ficha import leer_ficha, validar_cabecera, validar_procedencia


@dataclass(frozen=True)
class TablaLocal:
    """Archivo y columnas declaradas para una fuente de biblioteca local."""

    nombre: str
    archivo: str
    delimitador: str
    columnas: tuple[Column, ...]
    origen: str


def raiz_repositorio() -> Path:
    """Raíz del proyecto desde el que se invoca la CLI."""
    return Path.cwd().resolve()


def _dentro(ruta: Path, raiz: Path, nombre: str) -> Path:
    if ".." in ruta.parts:
        raise ValueError(f"{nombre}: ruta con .. no permitida")
    resuelta = (ruta if ruta.is_absolute() else raiz / ruta).resolve()
    if not resuelta.is_relative_to(raiz):
        raise ValueError(f"{nombre}: ruta fuera de la raíz del repositorio")
    return resuelta


def cargar_tablas_locales(ruta: Path, raiz: Path) -> dict[str, TablaLocal]:
    """Carga la configuración y sus fichas, con rutas confinadas a la raíz."""
    raiz = raiz.resolve()
    config = _dentro(ruta, raiz, "configuración")
    if not config.is_file():
        raise ValueError(f"no existe la configuración: {ruta}")
    datos = json.loads(config.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ValueError("la configuración de tablas locales debe ser un objeto")
    tablas = {}
    for nombre, descripcion in datos.items():
        if nombre.startswith("_"):
            continue
        if len(nombre.split(".")) != 2 or not all(p.isidentifier() for p in nombre.split(".")):
            raise ValueError(f"{nombre}: nombre de tabla inválido")
        if not isinstance(descripcion, dict):
            raise ValueError(f"{nombre}: configuración inválida")
        archivo = descripcion.get("archivo")
        delimitador = descripcion.get("delimitador")
        if (
            not isinstance(archivo, str)
            or not archivo
            or not isinstance(delimitador, str)
            or len(delimitador) != 1
        ):
            raise ValueError(f"{nombre}: archivo o delimitador inválido")
        csv = _dentro(Path(archivo), raiz, nombre)
        if not csv.is_file():
            raise ValueError(f"{nombre}: archivo no existe")
        ficha = _dentro(csv.with_suffix(".ficha.yaml"), raiz, nombre)
        if not ficha.is_file():
            raise ValueError(f"{nombre}: falta ficha del archivo")
        try:
            info = leer_ficha(ficha)
        except (yaml.YAMLError, TypeError, ValueError) as error:
            raise ValueError(f"{nombre}: ficha inválida") from error
        if not isinstance(info.tabla, str) or info.tabla.lower() != nombre.lower():
            raise ValueError(f"{nombre}: tabla inválida en ficha")
        if not isinstance(info.origen, str):
            raise ValueError(f"{nombre}: origen inválido en ficha")
        errores = validar_procedencia(info)
        if errores:
            raise ValueError(f"{nombre}: {'; '.join(errores)}")
        if (
            not isinstance(info.columnas, dict)
            or not info.columnas
            or any(not isinstance(n, str) or not n.isidentifier() for n in info.columnas)
            or len({n.casefold() for n in info.columnas}) != len(info.columnas)
            or any(not isinstance(t, str) or t not in TALEND_TYPES for t in info.columnas.values())
        ):
            raise ValueError(f"{nombre}: columnas o tipos inválidos en ficha")
        try:
            errores_cabecera = validar_cabecera(info, csv, delimitador)
        except (OSError, UnicodeError, csv_module.Error) as error:
            raise ValueError(f"{nombre}: no se pudo leer la cabecera del CSV") from error
        if errores_cabecera:
            raise ValueError(f"{nombre}: {errores_cabecera[0]}")
        columnas = tuple(Column(n, t, None, "fixture") for n, t in info.columnas.items())
        tablas[nombre.lower()] = TablaLocal(
            nombre.lower(), csv.relative_to(raiz).as_posix(), delimitador, columnas, info.origen
        )
    return tablas
