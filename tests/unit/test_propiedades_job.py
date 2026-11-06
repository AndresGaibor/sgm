"""Propiedades del Job (propósito, descripción, autor) y comentario de nodo (MG-P9-07, MG-P8-07).

Estos campos aún no se escriben en el `.item` ni en el `.properties`: los nombres de clave de Studio
no aparecen en ningún fixture del repositorio, y el parámetro COMMENT tampoco. Por eso las pruebas
fijan tres cosas: el valor por defecto vacío, que el texto libre se escapa como cualquier atributo
XML (`_atributo`) y que, mientras no haya formato verificado, la salida no cambia. La última prueba
debe reescribirse cuando se escriban los campos.
"""

from __future__ import annotations

from sgm.talend_item.componentes import log_row
from sgm.talend_item.item import _atributo, render_item, render_properties
from sgm.talend_item.modelo import Columna, Job, Nodo

RUTA_JAVA = r"C:\Talend\8.0.1\studio\configuration\lib\java"
FECHA = "2026-11-04T12:00:00.000-0500"
ESPECIALES = 'Tabla <A> & "B"\ncon salto\tTAB\r\nfin'


def _job(**propiedades: str) -> Job:
    nodo = log_row("tLogRow_1", [Columna("id", "id_Integer")], 120, 120, RUTA_JAVA)
    return Job("MCP_Propiedades", nodos=[nodo], **propiedades)


def test_los_campos_nuevos_valen_vacio_por_defecto():
    job = Job("MCP_Propiedades")
    assert (job.proposito, job.descripcion, job.autor) == ("", "", "")
    assert Nodo("tLogRow", "0.101", "tLogRow_1").comentario == ""


def test_con_campos_vacios_la_salida_no_cambia():
    sin = _job()
    vacio = _job(proposito="", descripcion="", autor="")
    assert render_item(sin) == render_item(vacio)
    assert render_properties(sin, fecha=FECHA) == render_properties(vacio, fecha=FECHA)


def test_el_texto_libre_se_escapa_como_atributo_xml():
    escapado = _atributo(ESPECIALES)
    assert "<" not in escapado and ">" not in escapado.replace("&gt;", "")
    assert "&lt;A&gt;" in escapado
    assert "&amp;" in escapado
    assert "&quot;B&quot;" in escapado
    assert "&#10;" in escapado and "&#09;" in escapado and "&#13;" in escapado
    assert "\n" not in escapado and "\t" not in escapado and "\r" not in escapado


def test_el_texto_escapado_sigue_siendo_xml_valido_en_un_atributo():
    import xml.etree.ElementTree as ET

    raiz = ET.fromstring(f'<x valor="{_atributo(ESPECIALES)}"/>')
    assert raiz.get("valor") == ESPECIALES


def test_mientras_no_hay_formato_verificado_los_campos_llenos_no_cambian_la_salida():
    """Guarda: si alguien escribe los campos sin verificar el formato, esta prueba falla."""
    vacio = _job()
    lleno = _job(proposito="Prueba", descripcion="Descripción <con> & comillas\"", autor="Andres")
    assert render_item(lleno) == render_item(vacio)
    assert render_properties(lleno, fecha=FECHA) == render_properties(vacio, fecha=FECHA)
