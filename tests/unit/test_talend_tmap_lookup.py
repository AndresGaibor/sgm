"""tMap con lookup (INNER JOIN), salida de rechazo y filtro: atributos del nodeData y conexiones."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from sgm.talend_item.conexiones import lookup
from sgm.talend_item.item import render_item
from sgm.talend_item.modelo import Columna, Conexion, Job
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

PRINCIPAL = [Columna("id", "id_Integer", nulable=False), Columna("tipo", "id_String")]
LOOKUP = [Columna("codigo", "id_String")]
EXPRESIONES = {"id": "row1.id", "tipo": "row1.tipo"}


def _tmap_con_union(
    expresiones_union: dict[str, str] | None = None,
    union_interna: bool = True,
    salidas: list[SalidaMap] | None = None,
):
    """`tMap` principal `row1` con un lookup `row2` unido por `row1.tipo == row2.codigo`."""
    if expresiones_union is None:
        expresiones_union = {"codigo": "row1.tipo"}
    entradas = [
        EntradaMap("row1", PRINCIPAL),
        EntradaMap(
            "row2",
            LOOKUP,
            expresiones_union=expresiones_union,
            union_interna=union_interna,
        ),
    ]
    if salidas is None:
        salidas = [
            SalidaMap("validos", PRINCIPAL, EXPRESIONES),
            SalidaMap("rechazados", PRINCIPAL, EXPRESIONES, rechazo_union=True),
        ]
    return tmap("tMap_1", entradas, salidas)


def _datos_del_item(nodo) -> ET.Element:
    """`nodeData` del `.item` completo, para comprobar lo que Studio leerá."""
    raiz = ET.fromstring(render_item(Job("Prueba", nodos=[nodo])))
    return raiz.find("node").find("nodeData")


def _entrada(datos: ET.Element, nombre: str) -> ET.Element:
    (entrada,) = [e for e in datos.findall("inputTables") if e.get("name") == nombre]
    return entrada


def _salida(datos: ET.Element, nombre: str) -> ET.Element:
    (salida,) = [s for s in datos.findall("outputTables") if s.get("name") == nombre]
    return salida


def test_el_lookup_lleva_innerjoin_y_la_expresion_de_union_de_su_columna():
    datos = _datos_del_item(_tmap_con_union())
    lookup_ = _entrada(datos, "row2")
    assert lookup_.get("innerJoin") == "true"
    assert lookup_.get("matchingMode") == "UNIQUE_MATCH"
    assert lookup_.get("lookupMode") == "LOAD_ONCE"
    (columna,) = lookup_.findall("mapperTableEntries")
    assert (columna.get("name"), columna.get("expression")) == ("codigo", "row1.tipo")


def test_la_entrada_principal_no_lleva_innerjoin_ni_expresiones():
    principal = _entrada(_datos_del_item(_tmap_con_union()), "row1")
    assert "innerJoin" not in principal.attrib
    assert all("expression" not in c.attrib for c in principal.findall("mapperTableEntries"))


def test_la_salida_de_rechazo_lleva_rejectinnerjoin_y_conector_reject():
    nodo = _tmap_con_union()
    datos = _datos_del_item(nodo)
    assert _salida(datos, "rechazados").get("rejectInnerJoin") == "true"
    assert "rejectInnerJoin" not in _salida(datos, "validos").attrib
    conectores = [(m.conector, m.nombre) for m in nodo.metadatas]
    assert conectores == [("FLOW", "validos"), ("REJECT", "rechazados")]


def test_el_filtro_y_el_rechazo_de_salida_se_escriben_con_sus_atributos():
    filtro = 'row1.tipo == "CC"'
    salida = SalidaMap("activos", PRINCIPAL, EXPRESIONES, rechazo=True, filtro=filtro)
    nodo = _tmap_con_union(salidas=[salida])
    activos = _salida(_datos_del_item(nodo), "activos")
    assert activos.get("reject") == "true"
    assert activos.get("activateExpressionFilter") == "true"
    assert activos.get("expressionFilter") == filtro
    assert nodo.metadatas[0].conector == "REJECT"


def test_una_expresion_de_union_vacia_falta_y_se_rechaza_con_su_columna():
    with pytest.raises(ValueError, match="codigo"):
        _tmap_con_union(expresiones_union={"codigo": "   "})


def test_una_columna_de_union_que_el_lookup_no_tiene_lanza_keyerror():
    with pytest.raises(KeyError, match="otra"):
        _tmap_con_union(expresiones_union={"otra": "row1.tipo"})


def test_un_inner_join_sin_expresiones_de_union_se_rechaza():
    with pytest.raises(ValueError, match="INNER JOIN"):
        _tmap_con_union(expresiones_union={})


def test_un_rechazo_de_union_sin_inner_join_se_rechaza():
    with pytest.raises(ValueError, match="INNER JOIN"):
        _tmap_con_union(union_interna=False)


def test_la_entrada_principal_no_puede_tener_union():
    entradas = [EntradaMap("row1", PRINCIPAL, union_interna=True)]
    with pytest.raises(ValueError, match="principal"):
        tmap("tMap_1", entradas, [SalidaMap("out1", PRINCIPAL, EXPRESIONES)])


def test_un_tmap_sin_entradas_se_rechaza():
    with pytest.raises(ValueError, match="entrada"):
        tmap("tMap_1", [], [SalidaMap("out1", PRINCIPAL, EXPRESIONES)])


def test_la_conexion_lookup_va_como_lookup_sin_unique_name():
    job = Job(
        "Prueba",
        nodos=[_tmap_con_union()],
        conexiones=[lookup("tFixedFlowInput_2", "tMap_1")],
    )
    (conexion,) = ET.fromstring(render_item(job)).findall("connection")
    assert conexion.get("connectorName") == "LOOKUP"
    assert conexion.get("lineStyle") == "8"
    assert conexion.get("label") == "row2"
    campos = [p.get("name") for p in conexion.findall("elementParameter")]
    assert campos == ["MONITOR_CONNECTION"]


def test_el_item_con_lookup_y_rechazo_es_xml_bien_formado_y_con_sus_conexiones():
    nodo = _tmap_con_union()
    conexiones: list[Conexion] = [
        lookup("tFixedFlowInput_2", "tMap_1"),
        Conexion("tMap_1", "tLogRow_1", "validos", "FLOW"),
        Conexion("tMap_1", "tLogRow_2", "rechazados", "REJECT"),
    ]
    raiz = ET.fromstring(render_item(Job("Prueba", nodos=[nodo], conexiones=conexiones)))
    tipos = [c.get("connectorName") for c in raiz.findall("connection")]
    assert tipos == ["LOOKUP", "FLOW", "REJECT"]
