"""Hito 88: el arnés de `v04` se comprueba sin Studio, hasta el `.item` generado."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from prueba_cuenta_gmf import (  # noqa: E402
    _N_VAR,
    _normalizacion,
    job_cuenta_gmf,
    reglas,
)

from sgm.talend_item.item import render_item  # noqa: E402
from sgm.talend_item.tmap import EntradaMap  # noqa: E402


def test_el_job_tiene_lectura_dos_tmaps_y_cuatro_salidas():
    job = job_cuenta_gmf()

    assert [n.unico for n in job.nodos] == [
        "tFileInputDelimited_1",
        "tMap_normalizacion",
        "tMap_filtros",
        "tFileOutputDelimited_1",
        "tFileOutputDelimited_2",
        "tFileOutputDelimited_3",
        "tFileOutputDelimited_4",
    ]
    assert len(job.conexiones) == 6
    assert [p.nombre for p in job.contextos["Default"]] == ["ruta_origen", "ruta_salida"]


def test_lee_las_23_columnas_var_del_csv_y_los_contextos_del_lanzador():
    job = job_cuenta_gmf()
    metadatas = job.nodos[0].metadatas

    assert metadatas is not None
    assert metadatas[0].conector == "FLOW"
    assert len(metadatas[0].columnas) == _N_VAR
    assert metadatas[0].columnas[0].nombre == "VAR1"
    assert metadatas[0].columnas[-1].nombre == "VAR23"


def test_la_normalizacion_proyecta_ocho_columnas_y_solo_gmf_se_convierte():
    r = reglas()
    columnas, expresiones = _normalizacion(r)

    assert [c.nombre for c in columnas] == [
        "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC",
        "GMF", "FIN_SALDO_CTA",
    ]
    assert expresiones["RELACION"] == "row1.VAR4"
    assert expresiones["FIN_SALDO_CTA"] == "row1.VAR23"
    assert "row1.VAR11" in expresiones["GMF"]
    assert "new java.math.BigDecimal" in expresiones["GMF"]
    assert "movePointLeft(0)" in expresiones["GMF"]
    assert "java.util.Objects.toString" in expresiones["GMF"]


def test_el_segundo_tmap_recibe_la_sabana_normalizada():
    job = job_cuenta_gmf()
    filtros = next(n for n in job.nodos if n.unico == "tMap_filtros")

    assert filtros.metadatas is not None
    assert [m.nombre for m in filtros.metadatas] == ["tipo_cta", "gmf", "valido", "cuenta"]
    assert [m.conector for m in filtros.metadatas] == ["FLOW"] * 4


def test_el_item_lleva_cuatro_filtros_y_cabecera_en_los_csv():
    item = render_item(job_cuenta_gmf())

    assert item.count('activateExpressionFilter="true"') == 4
    assert item.count('name="INCLUDEHEADER" value="true"') == 4
    assert "&quot;GMF NO NUMERICO&quot;" in item
    assert "Double.parseDouble" in item


def test_el_tmap_de_normalizacion_no_tiene_union_y_usa_la_entrada_principal():
    job = job_cuenta_gmf()
    metadatas = job.nodos[0].metadatas
    assert metadatas is not None
    entrada = EntradaMap("row1", list(metadatas[0].columnas))
    normalizacion = next(n for n in job.nodos if n.unico == "tMap_normalizacion")

    assert entrada.conexion == "row1"
    assert len(entrada.columnas) == _N_VAR
    assert not entrada.union_interna
    assert not entrada.expresiones_union
    assert normalizacion.metadatas is not None
    assert len(normalizacion.metadatas[0].columnas) == 8


def test_las_reglas_del_arnes_vienen_del_caso_no_de_constantes():
    r = reglas()

    assert r.informat == (3, 0)
    assert r.valores == ("1", "2", "3", "4", "5")
    assert r.motivos["lista"] == "TIPO CTA INVALIDO"
