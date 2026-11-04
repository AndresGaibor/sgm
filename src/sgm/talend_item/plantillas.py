"""Plantillas de componentes de Talend tomadas de nodos reales guardados por Studio.

Cada plantilla es un JSON en `plantillas/` con todos los parámetros de un nodo en el orden en que
Studio los escribe (ver `extraccion.py`). Instanciarla cambia solo los valores que se piden; los
demás quedan como los dejó Studio. Así no se inventa ningún parámetro, y un nombre que el componente
no tiene se rechaza en vez de ignorarse.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from sgm.talend_item.extraccion import COLUMNA_REF, UNICO
from sgm.talend_item.modelo import Columna, Fila, Metadata, Nodo, Tabla

DIRECTORIO = Path(__file__).parent / "plantillas"


@lru_cache(maxsize=None)
def cargar(componente: str) -> dict:
    ruta = DIRECTORIO / f"{componente}.json"
    if not ruta.exists():
        raise KeyError(f"No hay plantilla para {componente}: extraerla de un Job real")
    return json.loads(ruta.read_text(encoding="utf-8"))


def disponibles() -> list[str]:
    return sorted(p.stem for p in DIRECTORIO.glob("*.json"))


def _columnas(lista: list[dict]) -> tuple[Columna, ...]:
    return tuple(Columna(**c) for c in lista)


def _tabla(fila: dict, columnas: list[Columna], pedida: tuple | None) -> Tabla:
    if pedida is not None:
        celdas = tuple(pedida)
    elif "por_columna" in fila:
        resto = tuple((ref, valor) for ref, valor in fila["por_columna"])
        celdas = tuple(
            par for c in columnas for par in ((COLUMNA_REF, c.nombre), *resto)
        )
    else:
        celdas = tuple((ref, valor) for ref, valor in fila["celdas"])
    return Tabla(fila["tabla"], celdas, fila["show"])


def _metadatas(plantilla: dict, unico: str, columnas: list[Columna]) -> list[Metadata]:
    bloques: list[Metadata] = []
    for m in plantilla["metadatas"]:
        propias = _columnas(m["columnas"])
        if m.get("refleja_flow"):
            propias = (*columnas, *propias)
        elif not bloques:
            propias = tuple(columnas)
        bloques.append(Metadata(m["conector"], m["nombre"].replace(UNICO, unico), propias))
    return bloques


def nodo_desde_plantilla(
    componente: str,
    unico: str,
    x: int = 0,
    y: int = 0,
    valores: dict[str, str] | None = None,
    tablas: dict[str, tuple[tuple[str, str], ...]] | None = None,
    columnas: list[Columna] | None = None,
    ruta_java: str | None = None,
) -> Nodo:
    """Nodo de `componente` con los parámetros de la plantilla y los valores dados.

    `valores` cambia parámetros simples por nombre; `tablas`, los de tipo TABLE; `columnas`, el
    esquema del primer conector. Un nombre que la plantilla no tiene es un error.
    """
    plantilla = cargar(componente)
    valores, tablas, columnas = dict(valores or {}), dict(tablas or {}), list(columnas or [])
    parametros: list[Fila | Tabla] = []
    for fila in plantilla["parametros"]:
        if isinstance(fila, dict):
            parametros.append(_tabla(fila, columnas, tablas.pop(fila["tabla"], None)))
            continue
        campo, nombre, valor, show = fila
        if nombre == "UNIQUE_NAME":
            valor = unico
        elif nombre in valores:
            valor = valores.pop(nombre)
        elif nombre == "JAVA_LIBRARY_PATH" and ruta_java is not None:
            valor = ruta_java
        elif valor is not None:
            valor = valor.replace(UNICO, unico)
        parametros.append((campo, nombre, valor, show))
    sobran = sorted([*valores, *tablas])
    if sobran:
        raise KeyError(f"{componente} no tiene los parámetros {sobran}")
    metadatas = _metadatas(plantilla, unico, columnas)
    return Nodo(componente, str(plantilla["version"]), unico, x, y, parametros, metadatas=metadatas)
