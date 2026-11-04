"""Diseño deducido de un programa SAS: las secciones del documento de ocho secciones que ya existen.

Une el linaje, las fuentes y salidas, y lo declarado en `decisiones/`. Devuelve
`{codigo_seccion: {clave_de_fila: {columna: texto}}}`, el mismo contrato que usa la conformidad.
"""

from __future__ import annotations

from pathlib import Path

from sgm.agrupacion import cargar_declaracion
from sgm.flow.model import build_flows
from sgm.proceso.entradas_salidas import entradas_y_salidas
from sgm.proceso.secciones_entrada import cargar_declaradas, seccion_fuentes, seccion_salidas

Diseno = dict[str, dict[str, dict[str, str]]]
SECCIONES_EMITIDAS = ("1.1", "1.4")


def construir_diseno(programa: Path, agrupacion: Path, decisiones_diseno: Path) -> Diseno:
    """Secciones emitidas para `programa`, según las decisiones de agrupación y de diseño."""
    texto = programa.read_text(encoding="utf-8", errors="replace")
    modelo = build_flows({programa.name: texto})[programa.name]
    declaracion = cargar_declaracion(agrupacion)
    es = entradas_y_salidas(modelo, declaracion.productos)
    return {
        "1.1": seccion_fuentes(cargar_declaradas(decisiones_diseno, "fuentes"), es),
        "1.4": seccion_salidas(cargar_declaradas(decisiones_diseno, "salidas"), es),
    }
