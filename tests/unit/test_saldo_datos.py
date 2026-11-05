"""Hito 90 / R1-07: los comparadores de `v05` y de los vectores propios detectan un cambio.

Los esperados salen del corpus `v05_codex_saldos` y de la clasificación escrita a mano en
`VECTORES`. Ninguno se calcula con el traductor Java, así que estas pruebas no dependen de Studio.
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))

from saldo_datos import (  # noqa: E402
    CASO,
    ESTABLES,
    ESTABLES_NEG,
    PRODUCTOS,
    VECTORES,
    _proyectar,
    _suma,
    esperado,
    informe,
    invariantes,
    vector_csv,
)


def _obs_desde_corpus(producto: str) -> dict[str, list[tuple[str, ...]]]:
    """Un Job perfecto: las filas del corpus tal cual, con sus cinco tablas."""
    codex = _proyectar(CASO / "esperado" / f"RECHAZO_CODEX_{producto}.csv", ("NRO_CTA",))
    return {
        "neg": esperado(producto, "neg", ESTABLES_NEG),
        "valida": esperado(producto, "valida"),
        "codex": codex,
        "tipo": [],
    }


def test_el_corpus_cuadra_con_un_job_perfecto():
    for producto in PRODUCTOS:
        assert informe(producto, _obs_desde_corpus(producto))


def test_una_fila_de_saldo_cambiada_hace_fallar_el_informe():
    obs = _obs_desde_corpus("CTE")
    fila = list(obs["valida"][0])
    fila[ESTABLES.index("FIN_SALDO_CTA")] = "1"  # saldo cambiado a mano
    obs["valida"] = [tuple(fila), *obs["valida"][1:]]
    assert informe("CTE", obs) is False


def test_una_fila_de_rechazo_menos_hace_fallar_el_informe():
    obs = _obs_desde_corpus("AHO")
    obs["neg"] = obs["neg"][1:]
    assert informe("AHO", obs) is False


def test_la_invariante_del_corpus_cuadra_con_el_job_perfecto():
    resultados = {p: _obs_desde_corpus(p) for p in PRODUCTOS}
    assert invariantes(resultados) is True


def test_una_fila_que_no_vuelve_a_la_sabana_rompe_la_invariante():
    resultados = {p: _obs_desde_corpus(p) for p in PRODUCTOS}
    resultados["CTE"]["valida"] = resultados["CTE"]["valida"][1:]
    assert invariantes(resultados) is False


def test_los_vectores_tienen_veintitres_campos_y_saldo_al_final(tmp_path):
    ruta = vector_csv(tmp_path / "DETALLE_VECTORES.csv")
    filas = list(csv.reader(ruta.open(encoding="utf-8", newline=""), delimiter=";"))
    assert len(filas) == len(VECTORES)
    assert all(len(fila) == 23 for fila in filas)
    assert [fila[22] for fila in filas] == [v[4] for v in VECTORES]


def test_la_clasificacion_de_los_bordes_esta_escrita_a_mano():
    # Por NRO_CTA, no por saldo: el saldo "0" aparece en una fila válida y en una de codex.
    por_nro = {nro: (neg, valida) for _, _, _, nro, _, neg, valida in VECTORES}
    # Cero y -0.00 no son negativos; -0.01 sí. El faltante cuenta como menor que cero.
    assert por_nro["9000000102"] == (False, True)  # saldo 0
    assert por_nro["9000000105"] == (False, True)  # saldo -0.00
    assert por_nro["9000000106"] == (True, False)  # saldo -0.01
    assert por_nro["9000000103"] == (False, True)  # saldo 0.01
    assert por_nro["9000000104"] == (True, False)  # saldo faltante


def test_codex_y_negativo_salen_en_las_dos_tablas():
    # El rechazo de saldo no pasa por la cascada de codex: la fila de GMF 99 con saldo -5 sale
    # en INCONS_SALDO_NEG, y no en la sábana válida.
    fila = next(v for v in VECTORES if v[3] == "9000000108")
    assert fila[5] is True and fila[6] is False


def test_la_suma_de_decimales_es_exacta():
    filas = [("1000", "1", "1", "9", "0.01"), ("1000", "1", "1", "9", "-0.00")]
    assert _suma(filas) == Decimal("0.01")
