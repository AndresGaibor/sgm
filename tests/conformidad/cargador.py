"""Carga de la referencia manual (YAML) y lectura del documento Markdown de origen.

El cargador de la referencia vive en `sgm.conformidad.referencia`; aquí solo se reexporta para las
pruebas, junto con el conteo de filas del Markdown.
"""

from __future__ import annotations

import re
from pathlib import Path

from sgm.conformidad.referencia import (  # noqa: F401  (reexportados para las pruebas)
    CLASIFICACIONES,
    REFERENCIA,
    Fila,
    Seccion,
    cargar_secciones,
    todas_las_filas,
)

RAIZ = Path(__file__).resolve().parents[2]
DOCUMENTO = RAIZ / "docs" / "diseno-talend-exogena-depositos.md"


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
