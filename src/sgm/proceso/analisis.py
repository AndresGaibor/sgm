"""Análisis de regiones de un programa: texto normalizado, producto y familias.

Une `flow.regiones` (división por marcador) con `proceso.familias` (clones por producto). Los
sufijos y el marcador salen de la declaración del equipo, no del código.
"""

from __future__ import annotations

from dataclasses import dataclass

from sgm.agrupacion import Declaracion
from sgm.flow.regiones import Region, dividir_regiones
from sgm.proceso.familias import (
    UMBRAL_FAMILIA,
    ResultadoFamilias,
    detectar_familias,
    normalizar_region,
    producto_de_texto,
)


@dataclass(frozen=True)
class AnalisisRegiones:
    regiones: list[Region]
    producto: dict[int, str | None]
    normalizadas: dict[int, list[str]]
    familias: ResultadoFamilias


def analizar_regiones(
    texto: str, declaracion: Declaracion, umbral: float = UMBRAL_FAMILIA
) -> AnalisisRegiones:
    """Divide el programa en regiones, deduce su producto y agrupa las que son copias."""
    regiones = dividir_regiones(texto, declaracion.marcador)
    lineas = texto.split("\n")
    sufijos = [s for suf in declaracion.productos.values() for s in suf]
    textos = {r.indice: "\n".join(lineas[r.linea_inicio - 1 : r.linea_fin]) for r in regiones}
    normalizadas = {i: normalizar_region(t, sufijos) for i, t in textos.items()}
    producto = {i: producto_de_texto(t, declaracion.productos) for i, t in textos.items()}
    return AnalisisRegiones(
        regiones, producto, normalizadas, detectar_familias(normalizadas, producto, umbral)
    )
