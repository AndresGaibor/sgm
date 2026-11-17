"""B-17: cobertura explícita de `l6_13` a `l6_24` por el espacio de combinaciones de `OUTPUT`.

La cobertura es **de forma**: la estructura de ramas, los destinos por rama y la continuación del caso son las de
una combinación del espacio. No es de valores: el espacio fija sus condiciones (`VALOR <= 2`, `VALOR >= 4`) y los
casos usan otras (`valor = 1`, `valor = 2`), y el número de datasets del encabezado puede ser distinto. Por eso
no se compara el `esperado/` aquí; el intérprete ya se compara con el oráculo en `test_combinaciones_output.py`.

Los casos que el espacio no representa quedan listados con su motivo; no se cuentan como cubiertos.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_output.gramatica import Combinacion, combinaciones  # noqa: E402

# caso -> (rama, destinos por rama, continuación)
CUBIERTOS: dict[str, tuple[str, tuple[tuple[str, ...], ...], bool]] = {
    "l6_13_output_multiple_destinos": ("if_elseif", (("S1", "S2"), ("S3",)), False),
    "l6_16_output_condicional_sin_destino": ("if", ((),), False),
    "l6_17_output_sin_destino_en_punto_del_pdv": ("incondicional", ((),), True),
    "l6_18_output_condicional_sin_destino_con_continuacion": ("if", ((),), True),
    "l6_19_output_if_else_mismo_destino": ("if_else", (("S1",), ("S1",)), False),
    "l6_20_output_else_if_mismo_destino": ("if_elseif", (("S1",), ("S1",)), False),
    "l6_22_output_else_if_else_mismo_destino": (
        "if_elseif_else",
        (("S1",), ("S1",), ("S1",)),
        False,
    ),
    "l6_23_output_destino_en_primera_y_ultima_rama": (
        "if_elseif_else",
        (("S1",), ("S2",), ("S1",)),
        False,
    ),
    "l6_24_output_else_destinos_por_defecto": ("if_else", ((), ()), False),
}

# caso -> motivo por el que el espacio no lo representa
FUERA_DEL_ESPACIO: dict[str, str] = {
    "l6_14_output_en_puntos_del_pdv": (
        "dos OUTPUT seguidos con una asignación entre ellos: captura del PDV (B-17, BLOQUEOS)"
    ),
    "l6_15_output_condicional_con_continuacion": (
        "la asignación tras el primer OUTPUT cambia lo que escribe el segundo: captura del PDV"
    ),
    "l6_21_output_destinos_parcialmente_comunes": (
        "destinos (S1,S2) y (S2,S3): el par (S2,S3) no está en DESTINOS (B-17)"
    ),
}


def _espacio() -> set[Combinacion]:
    return set(combinaciones())


def test_todos_los_casos_l6_13_a_24_estan_clasificados():
    """Cada caso del rango está en una de las dos tablas, y no en las dos a la vez."""
    todos = {f"l6_{n}" for n in range(13, 25)}
    clasificados = {c.split("_output")[0] for c in CUBIERTOS} | {
        c.split("_output")[0] for c in FUERA_DEL_ESPACIO
    }
    assert clasificados == todos
    assert not set(CUBIERTOS) & set(FUERA_DEL_ESPACIO)


@pytest.mark.parametrize("caso", sorted(CUBIERTOS))
def test_la_forma_del_caso_es_una_combinacion_del_espacio(caso: str):
    rama, destinos, continuacion = CUBIERTOS[caso]
    assert Combinacion(rama, destinos, continuacion) in _espacio(), caso


@pytest.mark.parametrize("caso", sorted(FUERA_DEL_ESPACIO))
def test_los_casos_fuera_del_espacio_dan_su_motivo(caso: str):
    assert FUERA_DEL_ESPACIO[caso].strip(), caso
