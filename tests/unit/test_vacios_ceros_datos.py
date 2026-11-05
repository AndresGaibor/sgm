"""Hito 86 / R1-04: los esperados de `v02` son independientes del Job y se comparan fila por fila."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REAL = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
sys.path.insert(0, str(REPO / "tools"))

from vacios_ceros_datos import (  # noqa: E402
    ARCHIVOS,
    COLUMNAS,
    ESQUEMAS,
    PRODUCTOS,
    SALIDAS,
    VALIDO,
    anomalias,
    anomalias_plantadas,
    esperado,
    informe,
    invariantes,
    observado,
)


def test_las_23_columnas_son_las_que_emite_el_sas_real():
    """El esquema del arnés no se inventa: es el de `origenes_producto()` (hito 84)."""
    from sgm.proceso.origen_producto import origenes_producto

    texto = REAL.read_text(encoding="utf-8", errors="replace")
    origenes = origenes_producto(
        texto, {"cte": ("CTE", "CORRIENTE"), "aho": ("AHO", "AHORROS"), "nequi": ("NEQUI",)}
    )
    assert COLUMNAS == origenes.columnas_comunes
    assert len(COLUMNAS) == 23


def test_las_proyecciones_son_subconjuntos_del_esquema_y_la_de_validos_trae_el_saldo():
    assert set(ESQUEMAS["valido"]) <= set(COLUMNAS)
    assert set(ESQUEMAS["tit_cot"]) == set(ESQUEMAS["fa"])
    assert VALIDO[-1] == "FIN_SALDO_CTA"
    assert len(VALIDO) == len(ESQUEMAS["tit_cot"]) + 1
    assert set(ESQUEMAS) == set(SALIDAS) == set(ARCHIVOS)


def test_los_esperados_tienen_los_conteos_plantados_en_el_caso():
    for producto in PRODUCTOS:
        esp, plantadas = esperado(producto), anomalias_plantadas()[producto]
        assert len(esp["tit_cot"]) == plantadas["tit_cot_vacio"] + plantadas["tit_cot_cero"]
        assert len(esp["fa"]) == plantadas["fa_vacio"] + plantadas["fa_cero"]
        assert len(esp["valido"]) == plantadas["validos"]
        assert all(len(fila) == len(ESQUEMAS[modo]) for modo, filas in esp.items() for fila in filas)


def test_el_cero_de_fa_ausente_en_aho_es_cero_y_no_un_dato_perdido():
    plantadas = anomalias_plantadas()
    assert plantadas["CTE"]["fa_cero"] == 4
    assert plantadas["AHO"]["fa_cero"] == 0
    assert plantadas["AHO"]["validos"] == 70


def test_anomalias_separa_vacio_cero_y_otro_por_la_posicion_de_nro_doc():
    filas = [
        ("a", "b", "c", "d", "e", ""),
        ("a", "b", "c", "d", "e", "0"),
        ("a", "b", "c", "d", "e", "0"),
        ("a", "b", "c", "d", "e", "12"),
    ]
    assert anomalias(filas) == {"vacio": 1, "cero": 2, "otro": 1}


def test_observado_lee_los_tres_csv_sin_cabecera(tmp_path: Path):
    for nombre in SALIDAS.values():
        (tmp_path / nombre).write_text("1001,1,5000000001,L,T,0\n", encoding="utf-8")
    obs = observado(tmp_path)
    assert set(obs) == set(SALIDAS)
    assert all(filas == [("1001", "1", "5000000001", "L", "T", "0")] for filas in obs.values())


@pytest.mark.parametrize("producto", PRODUCTOS)
def test_informe_da_ok_cuando_lo_observado_es_lo_esperado(producto, capsys):
    esp = esperado(producto)
    assert informe(producto, esp, esp) is True
    salida = capsys.readouterr().out
    assert salida.count("OK") == len(ESQUEMAS) + 1
    assert "DIFERENCIA" not in salida


def test_informe_detecta_una_sola_fila_cambiada(capsys):
    esp = esperado("CTE")
    malo = {modo: list(filas) for modo, filas in esp.items()}
    fila = list(malo["valido"][0])
    fila[5] = "999999"
    malo["valido"][0] = tuple(fila)
    assert informe("CTE", esp, malo) is False
    salida = capsys.readouterr().out
    assert "DIFERENCIA" in salida
    assert "solo en esperado" in salida and "solo en obtenido" in salida


def test_informe_detecta_un_desglose_de_anomalias_equivocado(capsys):
    esp = esperado("CTE")
    malo = {modo: list(filas) for modo, filas in esp.items()}
    fila = list(malo["tit_cot"][0])
    fila[5] = "0" if fila[5] == "" else ""
    malo["tit_cot"][0] = tuple(fila)
    assert informe("CTE", esp, malo) is False
    salida = capsys.readouterr().out
    assert "anomalías plantadas" in salida
    assert "DIFERENCIA" in salida


def test_las_tres_invariantes_se_cumplen_con_los_esperados_reales(capsys):
    resultados = {p: esperado(p) for p in PRODUCTOS}
    assert invariantes(resultados) is True
    salida = capsys.readouterr().out
    assert "1024505 frente a 1024505" in salida
    assert "NO" not in salida


def test_las_invariantes_fallan_si_falta_una_fila_valida(capsys):
    resultados = {p: esperado(p) for p in PRODUCTOS}
    resultados["CTE"]["valido"] = resultados["CTE"]["valido"][1:]
    assert invariantes(resultados) is False
    assert "NO" in capsys.readouterr().out
