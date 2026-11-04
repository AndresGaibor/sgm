"""Esquema de un archivo delimitado sin cabecera, deducido de cómo el SAS lo renombra y convierte.

SAS nombra `VAR1`, `VAR2`, ... las columnas de un archivo sin cabecera. El programa las renombra
(`DATASET.VAR1 AS ANIO_PROCESO`) o las convierte (`NRO_CTA = input(left(VAR7), 30.)`). Esos dos
patrones demuestran el nombre de la columna; el segundo, además, que es numérica. Una columna que el
SAS nunca nombra conserva su `VARn` y es texto. No se supone ningún otro tipo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.fuentes_csv import FuenteCsv

_CONVERSION = re.compile(
    r"^\s*(\w+)\s*=\s*(?:COMPRESS\s*\(\s*)?INPUT\s*\(\s*LEFT\s*\(\s*VAR(\d+)\s*\)\s*,\s*\d+\.",
    re.IGNORECASE | re.MULTILINE,
)
_ALIAS = re.compile(r"\b(?:\w+\.)?VAR(\d+)\s+AS\s+(\w+)", re.IGNORECASE)


@dataclass(frozen=True)
class ColumnaCsv:
    posicion: int  # 1 para VAR1
    nombre: str  # el que el SAS demuestra, o VARn
    numerica: bool  # el SAS la convierte con input(): demostrado
    demostrada: bool  # el SAS le da nombre


def esquema_csv(texto: str, fuente: FuenteCsv) -> list[ColumnaCsv]:
    """Columnas 1..N de la fuente con el nombre y el tipo que el SAS demuestra."""
    segmento = texto[fuente.inicio : fuente.fin]
    nombres: dict[int, str] = {}
    numericas: set[int] = set()
    for m in _CONVERSION.finditer(segmento):
        n = int(m.group(2))
        nombres.setdefault(n, m.group(1))
        numericas.add(n)
    for m in _ALIAS.finditer(segmento):
        nombres.setdefault(int(m.group(1)), m.group(2))
    return [
        ColumnaCsv(n, nombres.get(n, f"VAR{n}"), n in numericas, n in nombres)
        for n in range(1, fuente.columnas + 1)
    ]
