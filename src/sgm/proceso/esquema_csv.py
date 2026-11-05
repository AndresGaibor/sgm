"""Esquema de un archivo delimitado sin cabecera, deducido de cómo el SAS lo renombra y convierte.

SAS nombra `VAR1`, `VAR2`, ... las columnas de un archivo sin cabecera. El programa las renombra
(`DATASET.VAR1 AS ANIO_PROCESO`) o las convierte (`NRO_CTA = input(left(VAR7), 30.)`). Esos dos
patrones demuestran el nombre de la columna; el segundo, además, que es numérica y con qué informat
`w.d` (ancho y decimales). Una columna que el SAS nunca nombra conserva su `VARn` y es texto.
No se supone ningún otro tipo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.fuentes_csv import FuenteCsv

_CONVERSION = re.compile(
    r"^\s*(\w+)\s*=\s*(?:COMPRESS\s*\(\s*)?INPUT\s*\(\s*LEFT\s*\(\s*VAR(\d+)\s*\)"
    r"\s*,\s*(\d+)\.(\d*)",
    re.IGNORECASE | re.MULTILINE,
)
_ALIAS = re.compile(r"\b(?:\w+\.)?VAR(\d+)\s+AS\s+(\w+)", re.IGNORECASE)


@dataclass(frozen=True)
class ColumnaCsv:
    posicion: int  # 1 para VAR1
    nombre: str  # el que el SAS demuestra, o VARn
    numerica: bool  # el SAS la convierte con input(): demostrado
    demostrada: bool  # el SAS le da nombre
    ancho: int = 0  # w del informat `w.d`; 0 si la columna no es numérica
    decimales: int = 0  # d del informat; 0 en `30.` y en columnas no numéricas


def esquema_csv(texto: str, fuente: FuenteCsv) -> list[ColumnaCsv]:
    """Columnas 1..N de la fuente con el nombre, el tipo y el informat que el SAS demuestra."""
    segmento = texto[fuente.inicio : fuente.fin]
    nombres: dict[int, str] = {}
    informats: dict[int, tuple[int, int]] = {}
    for m in _CONVERSION.finditer(segmento):
        n = int(m.group(2))
        nombres.setdefault(n, m.group(1))
        informats.setdefault(n, (int(m.group(3)), int(m.group(4) or 0)))
    for m in _ALIAS.finditer(segmento):
        nombres.setdefault(int(m.group(1)), m.group(2))
    return [
        ColumnaCsv(
            n,
            nombres.get(n, f"VAR{n}"),
            n in informats,
            n in nombres,
            *informats.get(n, (0, 0)),
        )
        for n in range(1, fuente.columnas + 1)
    ]
