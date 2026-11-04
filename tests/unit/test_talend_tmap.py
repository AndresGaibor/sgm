"""tMap de Talend: el bloque nodeData tiene la forma que Studio escribe en un Job real."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.talend_item.item import render_item
from sgm.talend_item.modelo import Columna, Job
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

FRAGMENTO_REAL = Path(__file__).resolve().parents[1] / "fixtures" / "talend" / "tmap_nodedata.xml"
ESPACIOS = (
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xmlns:TalendMapper="http://www.talend.org/mapper"'
)
XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"
COLUMNAS_ENTRADA = [Columna("id", "id_Integer", nulable=False), Columna("nombre", "id_String")]


def _raiz_nodedata(xml: str) -> ET.Element:
    """Parsea un `<nodeData>` suelto con los espacios de nombres que declara el Job."""
    return ET.fromstring(f"<raiz {ESPACIOS}>{xml}</raiz>")[0]


def _estructura(elemento: ET.Element) -> list[tuple[int, str, list[tuple[str, str]]]]:
    """Etiquetas, atributos en su orden y profundidad, en orden de documento."""
    salida: list[tuple[int, str, list[tuple[str, str]]]] = []

    def recorrer(e: ET.Element, profundidad: int) -> None:
        salida.append((profundidad, e.tag, list(e.attrib.items())))
        for hijo in e:
            recorrer(hijo, profundidad + 1)

    recorrer(elemento, 0)
    return salida


def _nodo_de_ejemplo():
    salida = SalidaMap(
        "out1",
        [
            Columna("id2", "id_Integer"),
            Columna("nombre_mayus", "id_String"),
            Columna("etiqueta", "id_String"),
        ],
        {
            "id2": "row1.id * 2",
            "nombre_mayus": "row1.nombre.toUpperCase()",
            "etiqueta": '"fila: " + row1.nombre',
        },
    )
    return tmap("tMap_1", [EntradaMap("row1", COLUMNAS_ENTRADA)], [salida], x=400, y=160)


def test_el_tmap_se_escribe_como_xml_valido_con_sus_entradas_y_salidas():
    nodo = _nodo_de_ejemplo()
    raiz = ET.fromstring(render_item(Job("Prueba", nodos=[nodo])))
    (xml_nodo,) = raiz.findall("node")
    datos = xml_nodo.find("nodeData")
    assert datos.get(XSI_TYPE) == "TalendMapper:MapperData"

    salida = datos.find("outputTables")
    assert salida.get("name") == "out1"
    assert [(e.get("name"), e.get("expression")) for e in salida.findall("mapperTableEntries")] == [
        ("id2", "row1.id * 2"),
        ("nombre_mayus", "row1.nombre.toUpperCase()"),
        ("etiqueta", '"fila: " + row1.nombre'),
    ]

    entrada = datos.find("inputTables")
    assert entrada.get("name") == "row1"
    assert entrada.get("matchingMode") == "UNIQUE_MATCH"
    assert entrada.get("lookupMode") == "LOAD_ONCE"
    assert [(e.get("name"), e.get("type")) for e in entrada.findall("mapperTableEntries")] == [
        ("id", "id_Integer"),
        ("nombre", "id_String"),
    ]

    assert [(m.get("connector"), m.get("name")) for m in xml_nodo.findall("metadata")] == [
        ("FLOW", "out1")
    ]
    assert [c.get("name") for c in xml_nodo.find("metadata").findall("column")] == [
        "id2",
        "nombre_mayus",
        "etiqueta",
    ]


def test_el_nodedata_tiene_las_etiquetas_atributos_y_orden_del_job_real():
    real = _raiz_nodedata(FRAGMENTO_REAL.read_text(encoding="utf-8"))
    columnas = [
        Columna("id", "id_Integer", nulable=False),
        Columna("nombre", "id_String", nulable=False),
        Columna("apellido", "id_String", nulable=False),
        Columna("ciudad", "id_String"),
        Columna("edad", "id_Integer"),
        Columna("salario", "id_BigDecimal"),
        Columna("fecha_registro", "id_Date"),
    ]
    expresiones = {c.nombre: f"row1.{c.nombre} " for c in columnas}
    nodo = tmap(
        "tMap_1",
        [EntradaMap("row1", columnas)],
        [SalidaMap("out1", columnas, expresiones)],
        x=400,
        y=160,
    )
    assert _estructura(_raiz_nodedata(nodo.datos)) == _estructura(real)


def test_una_columna_de_salida_sin_expresion_lanza_keyerror():
    salida = SalidaMap(
        "out1",
        [Columna("id2", "id_Integer"), Columna("nombre_mayus", "id_String")],
        {"id2": "row1.id * 2"},
    )
    with pytest.raises(KeyError, match="nombre_mayus"):
        tmap("tMap_1", [EntradaMap("row1", COLUMNAS_ENTRADA)], [salida])


def test_una_expresion_para_una_columna_que_la_salida_no_tiene_lanza_keyerror():
    salida = SalidaMap("out1", [Columna("id2", "id_Integer")], {"id2": "row1.id", "x": "1"})
    with pytest.raises(KeyError, match="'x'"):
        tmap("tMap_1", [EntradaMap("row1", COLUMNAS_ENTRADA)], [salida])


def test_un_tmap_sin_salidas_se_rechaza():
    with pytest.raises(ValueError, match="salida"):
        tmap("tMap_1", [EntradaMap("row1", COLUMNAS_ENTRADA)], [])
