"""Hito 89: el arnés del Job **emitido** se comprueba sin Studio.

No construye un Job a mano: `prueba_cuenta_real` emite con `sgm talend`, copia solo
`job_producto_0.1.item/.properties` y ejecuta CTE, AHO y VECTORES. Aquí se verifican los parámetros
del lanzador, los tres orígenes y el CSV de 23 columnas de los vectores propios.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from cuenta_real_datos import PRODUCTOS, SUFIJO_VECTORES, VECTORES  # noqa: E402
from prueba_cuenta_real import (  # noqa: E402
    EXTENSIONES,
    PROGRAMA,
    SUFIJOS,
    V01,
    _proyecto_tecnico,
    main,
    origenes,
    parametros,
)


def test_el_arnes_parte_del_programa_real_y_del_excel_de_v01():
    assert PROGRAMA.is_file()
    assert PROGRAMA.name == "client_large.sas"
    assert V01.is_dir()
    assert (V01 / "Homologacion_tpo_dto.xlsx").is_file()


def test_corre_tres_veces_el_mismo_job_emitido():
    assert SUFIJOS == (*PRODUCTOS, SUFIJO_VECTORES) == ("CTE", "AHO", "VECTORES")
    assert EXTENSIONES == (".item", ".properties")


def test_los_parametros_del_lanzador_incluyen_ruta_resultados(tmp_path):
    salida = tmp_path / "salida"
    origen = tmp_path / "DETALLE_CTE.csv"
    parametros_lanzador = parametros(salida, "CTE", origen)

    assert parametros_lanzador[0] == "producto=CTE"
    assert f"ruta_origen={origen.as_posix()}" in parametros_lanzador
    assert "sufijo=CTE" in parametros_lanzador
    assert f"ruta_resultados={salida.as_posix()}/" in parametros_lanzador
    assert "arch_hom_tipo_doc=Homologacion_tpo_dto.xlsx" in parametros_lanzador
    assert any(p.startswith("ruta_insumos=") and p.endswith("/") for p in parametros_lanzador)
    assert all("=" in p for p in parametros_lanzador)


def test_los_tres_origenes_son_los_del_corpus_y_el_csv_de_vectores(tmp_path):
    rutas = origenes(tmp_path)

    assert set(rutas) == set(SUFIJOS)
    for producto in PRODUCTOS:
        assert rutas[producto].is_file()
        assert rutas[producto].name == f"DETALLE_{producto}.csv"
    vector = rutas[SUFIJO_VECTORES]
    assert vector.is_file() and vector.name == "DETALLE_VECTORES.csv"
    filas = list(csv.reader(vector.open(encoding="utf-8", newline=""), delimiter=";"))
    assert len(filas) == len(VECTORES) == 8
    assert all(len(fila) == 23 for fila in filas)


def test_el_nombre_tecnico_del_proyecto_sale_de_talend_project(tmp_path):
    proyecto = tmp_path / "PRJ_BANCOLOMBIA"
    proyecto.mkdir()
    (proyecto / "talend.project").write_text(
        '<TalendProject technicalLabel="PRJ_BANCOLOMBIA_REAL"/>', encoding="utf-8"
    )

    assert _proyecto_tecnico(proyecto) == "PRJ_BANCOLOMBIA_REAL"
    assert _proyecto_tecnico(tmp_path / "sin-archivo") == "sin-archivo"


def test_un_directorio_que_no_es_proyecto_talend_no_se_valida(tmp_path):
    assert main(["--proyecto", str(tmp_path)]) == 2
