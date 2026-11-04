"""Tests del emisor de `.item`: compara contra un Job real guardado por Talend Studio 8.0.1."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from sgm.talend_item.componentes import fixed_flow_input, log_row
from sgm.talend_item.item import render_item, render_properties
from sgm.talend_item.modelo import Columna, Conexion, Job

REAL = Path(__file__).resolve().parents[1] / "fixtures" / "talend" / "hijo_0.1.item"
RUTA_JAVA = r"C:\Talend\8.0.1\studio\configuration\lib\java"
COLUMNAS = [Columna("id", "id_Integer"), Columna("ciudad", "id_String")]


def _job() -> Job:
    return Job(
        "MCP_L5_Hijo",
        nodos=[
            fixed_flow_input(
                "tFixedFlowInput_2",
                COLUMNAS,
                [["1", '"Bogota"'], ["2", '"Medellin"']],
                120,
                120,
                RUTA_JAVA,
            ),
            log_row("tLogRow_2", COLUMNAS, 320, 120, RUTA_JAVA),
        ],
        conexiones=[Conexion("tFixedFlowInput_2", "tLogRow_2")],
    )


def _despues_de_parametros(texto: str) -> str:
    return texto.split("</parameters>\n", 1)[1]


def _firmas(texto: str) -> list[tuple[str, str]]:
    """(campo, nombre) de cada parámetro de la sección `parameters`, en orden."""
    bloque = texto.split("<parameters>", 1)[1].split("</parameters>", 1)[0]
    return re.findall(r'field="([^"]*)" name="([^"]*)"', bloque)


def test_nodos_conexiones_y_subjobs_son_identicos_a_los_del_job_real():
    real = REAL.read_text(encoding="utf-8")
    assert _despues_de_parametros(render_item(_job())) == _despues_de_parametros(real)


def test_los_parametros_base_tienen_los_mismos_campos_y_orden_que_el_job_real():
    real = REAL.read_text(encoding="utf-8")
    assert _firmas(render_item(_job())) == _firmas(real)


def test_el_item_es_xml_bien_formado_con_los_dos_nodos_y_la_conexion():
    raiz = ET.fromstring(render_item(_job()))
    assert [n.get("componentName") for n in raiz.findall("node")] == ["tFixedFlowInput", "tLogRow"]
    (conexion,) = raiz.findall("connection")
    assert (conexion.get("source"), conexion.get("target")) == ("tFixedFlowInput_2", "tLogRow_2")
    assert len(raiz.findall("subjob")) == 1


def test_el_item_no_lleva_contrasenas_ni_rutas_locales():
    texto = render_item(_job())
    assert "enc:" not in texto
    assert "C:/Talend" not in texto and "/Applications" not in texto


def test_las_propiedades_son_estables_y_apuntan_al_item():
    a = render_properties(_job(), fecha="2026-11-04T12:00:00.000-0500")
    assert a == render_properties(_job(), fecha="2026-11-04T12:00:00.000-0500")
    raiz = ET.fromstring(a)
    ns = {"p": "http://www.talend.org/properties"}
    prop = raiz.find("p:Property", ns)
    assert prop.get("label") == "MCP_L5_Hijo" and prop.get("version") == "0.1"
    assert raiz.find("p:ProcessItem/process", ns).get("href") == "MCP_L5_Hijo_0.1.item#/"
    ids = re.findall(r'xmi:id="([^"]+)"', a)
    assert len(ids) == len(set(ids))
