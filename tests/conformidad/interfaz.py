"""Enganche entre la conformidad y el emisor del documento de diseño.

`obtener_diseno` llama a `sgm.proceso.diseno_doc.construir_diseno` con las decisiones del programa
(`decisiones/<programa>.agrupacion.yaml` y `decisiones/<programa>.diseno.yaml`). Solo devuelve las
secciones que el emisor ya produce (`SECCIONES_EMITIDAS`); las demás siguen en `xfail`.

Contrato de la salida: `{codigo_seccion: {clave_de_fila: {columna: texto}}}`, con los mismos
códigos de sección, claves de fila y nombres de columna que `diseno_manual.yaml`.
"""

from __future__ import annotations

from pathlib import Path

from sgm.conformidad.estado import diferencias_fila
from sgm.proceso.diseno_doc import SECCIONES_EMITIDAS, SECCIONES_GENERICAS, Diseno, construir_diseno
from tests.conformidad.cargador import RAIZ

__all__ = [
    "SECCIONES_EMITIDAS",
    "SECCIONES_GENERICAS",
    "Diseno",
    "diferencias_fila",
    "obtener_diseno",
]


def obtener_diseno(programa_sas: Path) -> Diseno:
    """Diseño que el migrador deduce de `programa_sas` (solo las secciones ya emitidas)."""
    decisiones = RAIZ / "decisiones"
    return construir_diseno(
        programa_sas,
        decisiones / f"{programa_sas.stem}.agrupacion.yaml",
        decisiones / f"{programa_sas.stem}.diseno.yaml",
    )
