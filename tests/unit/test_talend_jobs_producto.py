"""`job_producto`: lectura del archivo de origen, conversión del saldo y totales de origen."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.talend_item.arquitectura import ValidacionProducto, cargar_arquitectura
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


VALIDACION = ValidacionProducto(
    "tipo_documento",
    "TIPO_DOC",
    "CNAME",
    "TIPO_DOC_INVALIDO",
    "Homologación de tipo de documento",
    (("NEQUI", "Homologación de tipo de documento Nequi"),),
)


def test_la_arquitectura_lee_la_validacion_declarada(arq):
    (validacion,) = arq.validaciones
    assert (validacion.columna, validacion.columna_lookup) == ("TIPO_DOC", "CNAME")
    assert validacion.motivo == "TIPO_DOC_INVALIDO"


def test_nequi_usa_su_propio_excel_y_el_resto_el_comun():
    assert VALIDACION.fuente_de("NEQUI") == "Homologación de tipo de documento Nequi"
    assert VALIDACION.fuente_de("cte") == "Homologación de tipo de documento"


def test_con_validacion_el_job_replica_y_separa_validos_de_rechazados(arq):
    job = job_producto(
        arq, ("TIPO_DOC", "B", "FIN_SALDO_CTA"), validacion=VALIDACION
    )

    componentes = _componentes(job)
    assert {"tReplicate", "tFileInputExcel", "tFileOutputDelimited"} <= set(componentes)
    raiz = ET.fromstring(render_item(job))
    conectores = [(c.get("connectorName"), c.get("label")) for c in raiz.findall("connection")]
    assert ("LOOKUP", "row2") in conectores
    assert ("REJECT", "rechazados") in conectores


def test_la_salida_de_rechazos_lleva_el_motivo_y_el_sufijo(arq):
    job = job_producto(
        arq, ("TIPO_DOC", "B", "FIN_SALDO_CTA"), validacion=VALIDACION
    )

    texto = render_item(job)
    assert "doc_incorrectos_" in texto
    assert "context.sufijo" in texto
    assert "TIPO_DOC_INVALIDO" in texto  # el XML escapa las comillas del literal Java


def test_la_validacion_declara_las_variables_de_contexto_que_usa(arq):
    job = job_producto(
        arq, ("TIPO_DOC", "B", "FIN_SALDO_CTA"), validacion=VALIDACION
    )

    raiz = ET.fromstring(render_item(job))
    nombres = {p.get("name") for p in raiz.iter("contextParameter")}
    assert {"arch_hom_tipo_doc", "ruta_insumos", "ruta_resultados", "hoja_excel"} <= nombres


def test_sin_columna_de_saldo_solo_hay_conteo(arq):
    job = job_producto(arq, ("A", "B"))

    assert "tAggregateRow" in _componentes(job)
    assert not any("BigDecimal" in e for e in _atributos_de_expresion(job))
    codigo_xml = render_item(job)
    assert "suma_saldo_origen" not in codigo_xml
    assert '"sum"' not in codigo_xml and ">sum<" not in codigo_xml
