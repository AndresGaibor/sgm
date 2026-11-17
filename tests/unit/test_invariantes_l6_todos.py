"""Las invariantes de todos los casos L6 con `invariantes:` se cumplen sobre sus CSV.

`test_corpus_l4l6.py` solo recorre los casos de `ESPECIFICACIONES`; un caso nuevo (p. ej. `l6_32`,
hito 232m) quedaba sin esta comprobación. Esta prueba cubre el nivel completo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.invariantes import comprobar  # noqa: E402

CASOS_L6 = sorted(p.parent for p in (REPO / "tests" / "corpus" / "L6").glob("*/caso.yaml"))


@pytest.mark.parametrize("carpeta", CASOS_L6, ids=lambda c: c.name)
def test_invariantes_de_l6_se_cumplen(carpeta: Path) -> None:
    caso = cargar_caso(carpeta)
    if not caso.invariantes:
        pytest.skip("el caso no declara invariantes")
    fallos = comprobar(list(caso.invariantes), [caso.esperado, caso.entradas], caso.tolerancia)
    assert fallos == []
