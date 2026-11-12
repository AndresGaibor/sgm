"""El bloque `esquemas` de L3 a L8 sale del migrador: debe coincidir con lo que propone hoy (B-4).

Si cambia el código del migrador y los tipos demostrados cambian, esta prueba falla y la persona
revisa el bloque con `tools/proponer_esquemas_caso.py <carpeta>`. No se reescribe a ciegas.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import proponer_esquemas_caso as propuesta  # noqa: E402
from corpus_lib import esquemas_caso  # noqa: E402
from corpus_lib.caso import cargar_caso  # noqa: E402

CORPUS = REPO / "tests" / "corpus"
# L0 a L2 tienen bloques escritos a mano (pendientes con motivo): su revisión es otra tarea de B-4.
NIVELES = ("L3", "L4", "L5", "L6", "L8")
CASOS = [
    carpeta.parent
    for nivel in NIVELES
    for carpeta in sorted(CORPUS.glob(f"{nivel}/**/caso.yaml"))
]


@pytest.mark.parametrize("carpeta", CASOS, ids=lambda c: c.name)
def test_bloque_guardado_coincide_con_lo_que_propone_el_migrador(carpeta: Path) -> None:
    caso = cargar_caso(carpeta)
    guardado = caso.extra.get("esquemas")
    if not guardado:
        pytest.skip(f"{carpeta.name}: el programa no declara tablas con columnas")
    propuesto = propuesta.bloque_del_caso(carpeta)
    assert esquemas_caso.validar(guardado) == esquemas_caso.validar(propuesto)
