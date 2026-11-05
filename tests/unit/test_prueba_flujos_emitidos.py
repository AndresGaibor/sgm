"""Hito 87: el comparador del arnés de flujos emitidos, sin Studio.

La verdad sale de `v02_vacios_ceros/esperado/`; aquí solo se comprueba que el arnés reduce los CSV
de 19 columnas del Job emitido a las columnas estables por **nombre**, que detecta una fila que se
fue a otro flujo y que las tres invariantes se miden sobre lo que escribió el Job.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from prueba_flujos_emitidos import (  # noqa: E402
    ESTABLES,
    MODOS,
    _proyectar,
    esperado,
    informe,
    invariantes,
    observado,
    parametros,
)
from vacios_ceros_datos import ARCHIVOS, CASO, ESQUEMAS, PRODUCTOS  # noqa: E402

CABECERA_EMITIDA = (
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
    "VAL_CRED_MES", "NRO_CRED_MES", "PROM_CRED_MES", "MED_CRED_MES", "VAL_DEB_MES",
    "NRO_DEB_MES", "PROM_DEB_MES", "MED_SALDO_CTA", "PROM_SALDO_CTA", "MAX_SALDO_CTA",
    "MIN_SALDO_CTA", "FIN_SALDO_CTA",
)


def _fila_emitida(fila: tuple[str, ...]) -> tuple[str, ...]:
    """Una fila de `esperado/` reescrita en el esquema de 19 columnas del Job emitido.

    `LLAVE_NOMBRE` y `TIPO_DOC` quedan vacías por la normalización R1-02; las columnas que el
    comparador no mira se rellenan con ceros. No se toca ninguna de las columnas estables.
    """
    saldo = fila[6] if len(fila) > 6 else "0"
    return (fila[0], fila[1], fila[2], "", "", fila[5], *("0",) * 12, saldo)


def _filas_corpus(producto: str, modo: str) -> list[tuple[str, ...]]:
    with (CASO / "esperado" / ARCHIVOS[modo].format(p=producto)).open(
        encoding="utf-8", newline=""
    ) as archivo:
        return [tuple(f) for f in list(csv.reader(archivo, delimiter=","))[1:]]


@pytest.fixture
def salida(tmp_path) -> Path:
    """Los seis CSV que escribiría el Job emitido, derivados solo de `esperado/`."""
    for producto in PRODUCTOS:
        for modo in MODOS:
            filas = [_fila_emitida(f) for f in _filas_corpus(producto, modo)]
            with (tmp_path / ARCHIVOS[modo].format(p=producto)).open(
                "w", encoding="utf-8", newline=""
            ) as archivo:
                escritor = csv.writer(archivo, delimiter=",")
                escritor.writerow(CABECERA_EMITIDA)
                escritor.writerows(filas)
    return tmp_path


def test_el_esperado_se_proyecta_por_nombre_y_el_emitido_tambien(salida):
    for producto in PRODUCTOS:
        for modo in MODOS:
            assert observado(salida, producto, modo) == esperado(producto, modo)
            assert all(len(f) == len(ESTABLES[modo]) for f in esperado(producto, modo))


def test_el_informe_y_las_invariantes_cuadran_con_la_verdad_plantada(salida, capsys):
    resultados = {
        p: {m: observado(salida, p, m) for m in MODOS} for p in PRODUCTOS
    }
    assert all(informe(p, resultados[p]) for p in PRODUCTOS)
    assert invariantes(resultados)
    texto = capsys.readouterr().out
    assert "CTE tit_cot: esperadas 5 filas, obtenidas 5; OK" in texto
    assert "AHO fa: esperadas 2 filas, obtenidas 2; OK" in texto
    assert "suma saldo CTE=1024505 frente a 1024505" in texto


def test_un_nro_doc_equivocado_se_detecta(salida, capsys):
    ruta = salida / ARCHIVOS["tit_cot"].format(p="CTE")
    filas = _csv(ruta)
    filas[1] = (*filas[1][:5], "999", *filas[1][6:])
    _escribir(ruta, filas)
    resultados = {"CTE": {m: observado(salida, "CTE", m) for m in MODOS}}
    assert informe("CTE", resultados["CTE"]) is False
    assert "DIFERENCIA" in capsys.readouterr().out


def test_el_orden_de_las_columnas_del_csv_no_importa(tmp_path):
    ruta = tmp_path / "otro.csv"
    _escribir(ruta, [("NRO_DOC", "RELACION", "TIPO_CTA", "NRO_CTA"),
                     ("0", "1001", "1", "5000000001")])
    assert _proyectar(ruta, ESTABLES["tit_cot"]) == [("1001", "1", "5000000001", "0")]


def test_una_columna_que_falta_no_se_silencia(tmp_path):
    ruta = tmp_path / "mal.csv"
    _escribir(ruta, [("RELACION", "TIPO_CTA"), ("1001", "1")])
    with pytest.raises(RuntimeError, match="no trae las columnas"):
        _proyectar(ruta, ESTABLES["tit_cot"])


def test_los_parametros_usan_el_csv_de_v02_y_el_excel_de_v01(tmp_path):
    texto = " ".join(parametros(tmp_path, "CTE"))
    assert "v02_vacios_ceros/entradas/DETALLE_CTE.csv" in texto
    assert "v01_tipo_doc/entradas/" in texto
    assert "sufijo=CTE" in texto
    assert "ruta_resultados=" in texto


def test_los_esquemas_del_corpus_siguen_siendo_la_proyeccion_declarada():
    assert [len(ESQUEMAS[m]) for m in MODOS] == [6, 6, 7]


def _csv(ruta: Path) -> list[tuple[str, ...]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return [tuple(f) for f in csv.reader(archivo, delimiter=",")]


def _escribir(ruta: Path, filas: list[tuple[str, ...]]) -> None:
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        csv.writer(archivo, delimiter=",").writerows(filas)
