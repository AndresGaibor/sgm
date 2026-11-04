"""Pendientes del diseño: lo que el SAS no demuestra, cada uno con su motivo.

Nada se adivina: cada línea dice qué falta y por qué. Las decisiones humanas (por ejemplo si dos
copias son el mismo proceso) se listan aquí para que una persona las confirme.
"""

from __future__ import annotations

from sgm.proceso.analisis import AnalisisRegiones
from sgm.proceso.entradas_salidas import EntradasSalidas
from sgm.proceso.etapas import Cobertura

Pendiente = tuple[str, str]  # (qué, motivo)


def reunir_pendientes(
    es: EntradasSalidas, regiones: AnalisisRegiones, etapas: Cobertura | None
) -> list[Pendiente]:
    """Pendientes de entradas, regiones sin copia, copias repetidas y etiquetas sin etapa."""
    filas: list[Pendiente] = [(p.nombre, p.motivo) for p in es.pendientes]
    for familia in regiones.familias.familias:
        if familia.productos_repetidos:
            productos = ", ".join(familia.productos_repetidos)
            filas.append(
                (
                    f"familia {familia.id}: varias regiones del producto {productos}",
                    "el producto no distingue las copias: hay que declarar el parámetro",
                )
            )
    for indice in regiones.familias.unicas:
        producto = regiones.producto.get(indice) or "sin producto"
        filas.append(
            (
                f"región {indice} ({producto}, {len(regiones.normalizadas[indice])} líneas)",
                "sin copia en otro producto: proceso propio, la equivalencia es decisión humana",
            )
        )
    if etapas and etapas.sin_etapa:
        distintas = sorted(set(etapas.sin_etapa))
        filas.append(
            (
                f"{len(etapas.sin_etapa)} etiquetas sin etapa ({len(distintas)} distintas)",
                "ningún patrón de `etapas` las cubre: " + "; ".join(distintas[:8]),
            )
        )
    return filas
