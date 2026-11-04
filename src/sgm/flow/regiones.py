"""Regiones de un programa SAS: tramos del archivo delimitados por una línea marcador.

Una región va de una aparición del marcador a la siguiente. Lo que hay antes del primer marcador
pertenece a la región 0, junto con ese marcador. Cada paso se asigna a la región de la línea de su
llamada de macro (si la tiene) o, si no, a la línea de su evidencia. Así un paso que sale de una
macro definida en otra región queda donde el programa la invoca.

El marcador no es un literal del código: llega como parámetro desde el YAML de decisiones
(`decisiones/<programa>.agrupacion.yaml`).
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field

from sgm.flow.model import FlowModel, FlowStep

# Comentario de etiqueta: `/* Etiqueta: texto */`. Puede ocupar varias líneas.
_ETIQUETA = re.compile(r"/\*\s*Etiqueta:\s*(.*?)\s*\*/", re.IGNORECASE | re.DOTALL)
# Número de línea dentro de la clave de una llamada: "línea:nombre" o "archivo:línea:nombre".
_LINEA_LLAMADA = re.compile(r"(?:^|:)(\d+):[^:]+$")


@dataclass
class Region:
    """Un tramo del archivo, con sus líneas (1-based, inclusive) y sus etiquetas en orden."""

    indice: int
    linea_inicio: int
    linea_fin: int
    etiquetas: list[str] = field(default_factory=list)


def _patron_marcador(marcador: str) -> re.Pattern[str]:
    """Patrón que casa el marcador al inicio de línea, sin importar mayúsculas ni espacios."""
    partes = [re.escape(p) for p in marcador.split()]
    if not partes:
        raise ValueError("el marcador de región no puede estar vacío")
    # Tras el marcador no puede seguir un carácter de nombre: "%macro ambiente" no casa con
    # "%macro ambiente_cte".
    return re.compile(r"^\s*" + r"\s+".join(partes) + r"(?!\w)", re.IGNORECASE)


def dividir_regiones(texto: str, marcador: str) -> list[Region]:
    """Regiones del texto según las líneas que empiezan con el marcador.

    Con k marcadores hay k regiones: la región 0 va de la línea 1 hasta antes del segundo marcador,
    y la región j (j >= 1) empieza en el marcador j+1. Sin marcadores hay una sola región.
    """
    lineas = texto.split("\n")
    # El salto final no abre una línea nueva: un archivo "a\nb\n" tiene dos líneas.
    if len(lineas) > 1 and lineas[-1] == "":
        lineas.pop()
    total = max(len(lineas), 1)
    patron = _patron_marcador(marcador)
    marcas = [i + 1 for i, linea in enumerate(lineas) if patron.match(linea)]
    # El primer marcador no abre región: la región 0 ya empieza en la línea 1.
    inicios = [1] + marcas[1:]
    regiones: list[Region] = []
    for indice, inicio in enumerate(inicios):
        fin = inicios[indice + 1] - 1 if indice + 1 < len(inicios) else total
        regiones.append(Region(indice, inicio, max(fin, inicio)))
    for m in _ETIQUETA.finditer(texto):
        linea = texto.count("\n", 0, m.start()) + 1
        region = regiones[region_de_linea(regiones, linea)]
        region.etiquetas.append(" ".join(m.group(1).split()))
    return regiones


def region_de_linea(regiones: list[Region], linea: int) -> int:
    """Índice de la región que contiene la línea; fuera del rango se usa el borde más cercano."""
    inicios = [r.linea_inicio for r in regiones]
    return min(max(bisect.bisect_right(inicios, linea) - 1, 0), len(regiones) - 1)


def _linea_de_llamada(macro_call: str | None) -> int | None:
    """Línea de la llamada de macro, si la clave la trae ("línea:nombre" en `build_flow`)."""
    if not macro_call:
        return None
    found = _LINEA_LLAMADA.search(macro_call)
    return int(found.group(1)) if found else None


def region_de_paso(paso: FlowStep, regiones: list[Region]) -> int:
    """Índice de región de un paso: la de su llamada de macro si la tiene, si no la de su línea."""
    linea = _linea_de_llamada(paso.outer_call or paso.macro_call)
    if linea is None:
        linea = paso.line
    return regiones[region_de_linea(regiones, linea)].indice


def asignar_regiones(modelo: FlowModel, regiones: list[Region]) -> dict[str, int]:
    """Índice de región de cada paso del modelo, por id de paso."""
    return {paso.id: region_de_paso(paso, regiones) for paso in modelo.steps}
