"""`job_producto`: lectura del archivo de origen, conversión del saldo y totales de origen."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.item import render_item
from sgm.talend_item.jobs_producto import job_producto

RAIZ = Path(__file__).resolve().parents[2]
DECISIONES = RAIZ / "decisiones" / "client_large.jobs.yaml"


@pytest.fixture(scope="module")
def arq():
    return cargar_arquitectura(DECISIONES)


def _componentes(job) -> list[str]:
    raiz = ET.fromstring(render_item(job))
    return [n.get("componentName") for n in raiz.iter("node")]


def _atributos_de_expresion(job) -> list[str]:
    raiz = ET.fromstring(render_item(job))
    return [e.get("expression") for e in raiz.iter() if e.get("expression") is not None]


def test_con_saldo_el_job_lee_convierte_suma_e_imprime(arq):
    job = job_producto(arq, ("A", "B", "FIN_SALDO_CTA"))

    componentes = _componentes(job)
    assert "tFileInputDelimited" in componentes
    assert "tMap" in componentes
    assert "tAggregateRow" in componentes
    assert "tLogRow" in componentes


def test_la_expresion_del_tmap_convierte_el_saldo_con_bigdecimal(arq):
    job = job_producto(arq, ("A", "B", "FIN_SALDO_CTA"))

    expresiones = _atributos_de_expresion(job)
    saldo = [e for e in expresiones if "BigDecimal" in e]
    assert len(saldo) == 1
    assert "row1.FIN_SALDO_CTA" in saldo[0]
    assert "new java.math.BigDecimal(" in saldo[0]


def test_el_contexto_declara_producto_ruta_origen_y_sufijo(arq):
    job = job_producto(arq, ("A", "B", "FIN_SALDO_CTA"))

    raiz = ET.fromstring(render_item(job))
    nombres = {p.get("name") for p in raiz.iter("contextParameter")}
    assert {"producto", "ruta_origen", "sufijo"} <= nombres


def test_sin_columna_de_saldo_solo_hay_conteo(arq):
    job = job_producto(arq, ("A", "B"))

    assert "tAggregateRow" in _componentes(job)
    assert not any("BigDecimal" in e for e in _atributos_de_expresion(job))
    codigo_xml = render_item(job)
    assert "suma_saldo_origen" not in codigo_xml
    assert '"sum"' not in codigo_xml and ">sum<" not in codigo_xml
