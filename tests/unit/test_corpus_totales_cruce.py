"""Casos L8 de totales: el esperado coincide con lo plantado y con el cruce SQL.

Complementa `test_corpus_totales.py`. Aquí se comparan los CSV de `esperado/` con los conteos
plantados (`anomalias_plantadas`), con los estados de conciliación y con el cruce que ejecuta el
programa SAS sobre SQLite (`totales_cruce_casos.py`). Los bloqueos del oráculo (convención de
vacío, ROUND, IS MISSING con cadena vacía) son `xfail` estrictos: si se arreglan, la prueba avisa.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "corpus_datos"))
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.csv_tabla import leer_csv  # noqa: E402
from corpus_lib.traduccion_sql import a_sqlite  # noqa: E402
from totales_cruce_casos import cruzar  # noqa: E402

CASOS_DIR = REPO / "tests" / "corpus" / "L8" / "totales"
IDS = [p.name for p in sorted(CASOS_DIR.iterdir()) if (p / "caso.yaml").is_file()]
MOTIVO_CONVENCION = ("oráculo: la celda vacía es NULL y NRO_CTA = '' no la cuenta; SAS sí "
                     "(el blanco es igual a ''). Ver observacion_revision de 03 y 08.")
BLOQUEADOS = {"03_sabana_nal_ext": MOTIVO_CONVENCION, "08_cadena_completa_macros": MOTIVO_CONVENCION}


def _yaml(id_: str) -> dict:
    return yaml.safe_load((CASOS_DIR / id_ / "caso.yaml").read_text(encoding="utf-8"))


def _valor(id_: str, nombre: str, columna: str) -> float:
    """Valor numérico de la primera fila de una tabla de `esperado/` (vacío cuenta como 0)."""
    cabecera, filas = leer_csv(CASOS_DIR / id_ / "esperado" / f"{nombre}.csv")
    return float(filas[0][cabecera.index(columna)] or 0)


# (caso, tabla, columna, clave de anomalias_plantadas) que deben coincidir con `esperado/`.
CONTEOS = [
    ("01_duplicados_frecuencias", "CONTROL_DUPLICADOS_AHO", "NRO_REGISTROS_ORIGEN", "filas_origen"),
    ("01_duplicados_frecuencias", "CONTROL_DUPLICADOS_AHO", "NRO_LLAVES_UNICAS", "llaves_unicas"),
    ("01_duplicados_frecuencias", "CONTROL_DUPLICADOS_AHO", "NRO_REGISTROS_DUPLICADOS",
     "extra_segun_case_original"),
    ("01_duplicados_frecuencias", "SUMA_SALDO_ORIGEN_AHO", "SUMA_SALDO_ORIGEN", "suma_saldo_origen"),
    ("02_inconsistencias_correccion", "CONTROL_INCONS_AHO", "NRO_REGISTROS_INCONS_CORREGIDOS",
     "filas_corregibles"),
    ("02_inconsistencias_correccion", "CONTROL_INCONS_AHO", "NRO_INCONS_POR_CORREGIR",
     "filas_por_corregir"),
    ("02_inconsistencias_correccion", "CONTROL_INCONS_AHO", "NRO_REG_SABANA_FINAL",
     "filas_sabana_final"),
    ("02_inconsistencias_correccion", "SUMA_SABANA_AHO", "SUMA_SALDO_SABANA_FINAL",
     "suma_saldo_sabana_final"),
    ("03_sabana_nal_ext", "CONTROL_SABANA_AHO", "NRO_RESULTADO_NAL", "filas_resultado_nal"),
    ("03_sabana_nal_ext", "CONTROL_SABANA_AHO", "NRO_RESULTADO_EXT", "filas_resultado_ext"),
    ("03_sabana_nal_ext", "CONTROL_SABANA_AHO", "NRO_FILAS_SIN_CUENTA", "filas_sin_cuenta"),
    ("03_sabana_nal_ext", "SUMA_NAL_AHO", "SUMA_SALDO_NAL", "suma_saldo_resultado_nal"),
    ("03_sabana_nal_ext", "SUMA_EXT_AHO", "SUMA_SALDO_EXT", "suma_saldo_resultado_ext"),
    ("04_totales_origen_salida", "TOTAL_ORIGEN_CTE", "SUMA_SALDO_ORIGEN", "cte_suma_saldo_origen"),
    ("04_totales_origen_salida", "TOTAL_SALIDA_CTE", "NRO_FILAS_SALIDA", "cte_filas_salida"),
    ("04_totales_origen_salida", "TOTAL_SALIDA_AHO", "SUMA_SALDO_SALIDA", "aho_suma_saldo_salida"),
    ("05_conciliacion", "CONCILIACION_CTE", "DIF_FILAS", "cte_diferencia_filas"),
    ("05_conciliacion", "CONCILIACION_AHO", "DIF_SALDO", "aho_diferencia_saldo"),
    ("06_periodo_fecha", "CUENTA_PERIODO_AHO", "NRO_REGISTROS_PERIODO", "filas_del_periodo"),
    ("07_impala_lectura", "CONTROL_IMPALA", "NRO_FILAS_ULTIMO_DIA", "filas_ultimo_dia"),
    ("07_impala_lectura", "CONTROL_IMPALA", "NRO_MCDQ_ULTIMO_DIA", "filas_mcdq_ultimo_dia"),
    ("08_cadena_completa_macros", "TOTALES_CTE", "NRO_ORIGEN", "cte_filas_origen"),
    ("08_cadena_completa_macros", "TOTALES_CTE", "NRO_UNICOS", "cte_filas_tras_dedup"),
    ("08_cadena_completa_macros", "TOTALES_CTE", "NRO_SABANA", "cte_filas_sabana"),
    ("08_cadena_completa_macros", "TOTALES_CTE", "SUMA_SABANA", "cte_suma_saldo_sabana"),
    ("08_cadena_completa_macros", "CONCILIACION_AHO", "DIF_SIN_DUPLICADOS_EXACTOS",
     "aho_dif_sin_duplicados_exactos"),
]


@pytest.mark.parametrize(("id_", "tabla", "columna", "clave"), CONTEOS)
def test_esperado_coincide_con_anomalias_plantadas(id_: str, tabla: str, columna: str,
                                                   clave: str) -> None:
    anomalias = _yaml(id_)["anomalias_plantadas"]
    assert _valor(id_, tabla, columna) == pytest.approx(float(anomalias[clave]), abs=0.005)


def test_estados_de_conciliacion_del_esperado() -> None:
    """Los CASE de 05 y 08 se leen del esperado con la regla del programa."""
    anomalias = _yaml("05_conciliacion")["anomalias_plantadas"]
    for prod in ("CTE", "AHO"):
        dif_filas = _valor("05_conciliacion", f"CONCILIACION_{prod}", "DIF_FILAS")
        dif_saldo = _valor("05_conciliacion", f"CONCILIACION_{prod}", "DIF_SALDO")
        concilia = abs(dif_saldo) <= 0.01 and dif_filas == 0
        assert anomalias[f"{prod.lower()}_estado"] == ("CONCILIA" if concilia else "NO CONCILIA")
    anomalias = _yaml("08_cadena_completa_macros")["anomalias_plantadas"]
    for prod in ("CTE", "AHO"):
        dif_total = _valor("08_cadena_completa_macros", f"CONCILIACION_{prod}", "DIF_TOTAL")
        estado = "CONCILIA" if abs(dif_total) <= 0.01 else "NO CONCILIA"
        assert anomalias[f"{prod.lower()}_estado"] == estado


CRUCE = [
    pytest.param(i, marks=pytest.mark.xfail(strict=True, reason=BLOQUEADOS[i]))
    if i in BLOQUEADOS else i
    for i in IDS
]


@pytest.mark.parametrize("id_", CRUCE)
def test_cruce_con_el_oraculo_sql(id_: str) -> None:
    """Lo que el programa hace con SQL, ejecutado en SQLite, coincide con `esperado/`."""
    resultado, diferencias, _ = cruzar(id_, CASOS_DIR / id_)
    assert resultado.tablas, "el cruce debe producir al menos una tabla"
    assert diferencias == []


@pytest.mark.parametrize("id_", ["03_sabana_nal_ext", "08_cadena_completa_macros"])
def test_cadena_vacia_coincide_con_sas_en_03_y_08(id_: str) -> None:
    """Con cadena vacía el cruce coincide en 03 y 08: el fallo es la convención del oráculo."""
    _, diferencias, _ = cruzar(id_, CASOS_DIR / id_, vacio_nulo=False)
    assert diferencias == []


@pytest.mark.xfail(strict=True, reason="oráculo: con cadena vacía falla el IS MISSING del LEFT "
                   "JOIN de 02; la fila sin cuenta no sale de la sábana. Ver observacion_revision.")
def test_cruce_de_02_con_cadena_vacia() -> None:
    caso = CASOS_DIR / "02_inconsistencias_correccion"
    _, diferencias, _ = cruzar("02_inconsistencias_correccion", caso, vacio_nulo=False)
    assert diferencias == []


def test_macros_de_conciliacion_por_into() -> None:
    """Los INTO del estado se resuelven en el cruce: CONCILIA y NO CONCILIA, como el programa."""
    resultado, _, _ = cruzar("05_conciliacion", CASOS_DIR / "05_conciliacion")
    assert resultado.macros["estado_cte"] == "CONCILIA"
    assert resultado.macros["estado_aho"] == "NO CONCILIA"


@pytest.mark.xfail(strict=True, reason="oráculo: ROUND(x, 0.01) se traduce como round(x, 0.01) de "
                   "SQLite, que trunca el 0.01 a entero; SAS redondea al centavo.")
def test_round_a_centavo_en_el_oraculo() -> None:
    sql = a_sqlite("SELECT ROUND(12.345, 0.01) AS r")
    assert sqlite3.connect(":memory:").execute(sql).fetchone()[0] == pytest.approx(12.35)
