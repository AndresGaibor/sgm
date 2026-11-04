"""Plantillas de los componentes validados en Talend Studio con un Job de referencia.

Cada prueba instancia la plantilla con valores típicos y comprueba lo esencial del XML que sale.
Los Jobs de referencia se compilaron, exportaron y ejecutaron en Studio 8.0.1 (ver el reporte del hito).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from sgm.talend_item.componentes import log_row
from sgm.talend_item.conexiones import si
from sgm.talend_item.item import render_item
from sgm.talend_item.modelo import Columna, Conexion, Job
from sgm.talend_item.plantillas import nodo_desde_plantilla

ENTRADA = [Columna("id", "id_Integer"), Columna("nombre", "id_String"), Columna("cantidad", "id_Integer")]
CATCHER = [
    Columna("moment", "id_Date"),
    Columna("pid", "id_String"),
    Columna("root_pid", "id_String"),
    Columna("father_pid", "id_String"),
    Columna("project", "id_String"),
    Columna("job", "id_String"),
    Columna("context", "id_String"),
    Columna("priority", "id_Integer"),
    Columna("type", "id_String"),
    Columna("origin", "id_String"),
    Columna("message", "id_String"),
    Columna("code", "id_Integer"),
]


def _xml(nodos, conexiones=()):
    """Renderiza un Job con los nodos dados y devuelve su raíz XML (valida que sea XML bien formado)."""
    return ET.fromstring(render_item(Job("Prueba", nodos=list(nodos), conexiones=list(conexiones))))


def _parametros(nodo_xml):
    """Parámetros simples del nodo como diccionario nombre -> valor."""
    return {p.get("name"): p.get("value") for p in nodo_xml.findall("elementParameter")}


def _tabla(nodo_xml, nombre):
    """Pares (elementRef, value) de una tabla del nodo, en orden."""
    tabla = next(p for p in nodo_xml.findall("elementParameter") if p.get("name") == nombre)
    return [(v.get("elementRef"), v.get("value")) for v in tabla.findall("elementValue")]


def _columnas(nodo_xml, conector="FLOW"):
    meta = next(m for m in nodo_xml.findall("metadata") if m.get("connector") == conector)
    return [c.get("name") for c in meta.findall("column")]


def test_tfileinputexcel_lee_xlsx_con_su_hoja_cabecera_y_rechazo():
    nodo = nodo_desde_plantilla(
        "tFileInputExcel",
        "tFileInputExcel_1",
        valores={"FILENAME": '"C:/datos/entrada.xlsx"', "VERSION_2007": "true", "HEADER": "1",
                 "PASSWORD": '"***"'},  # marcador: con VERSION_2007 Studio exige un valor no vacío
        tablas={"SHEETLIST": (("SHEETNAME", '"Datos"'), ("USE_REGEX", "false"))},
        columnas=ENTRADA,
    )
    raiz = _xml([nodo])
    (xml_nodo,) = raiz.findall("node")
    params = _parametros(xml_nodo)
    assert xml_nodo.get("componentName") == "tFileInputExcel"
    assert xml_nodo.get("componentVersion") == "0.102"
    assert params["FILENAME"] == '"C:/datos/entrada.xlsx"'
    assert params["VERSION_2007"] == "true"
    assert params["HEADER"] == "1"
    assert _tabla(xml_nodo, "SHEETLIST") == [("SHEETNAME", '"Datos"'), ("USE_REGEX", "false")]
    assert _columnas(xml_nodo) == ["id", "nombre", "cantidad"]
    assert _columnas(xml_nodo, "REJECT") == ["id", "nombre", "cantidad", "errorCode", "errorMessage"]


def test_taggregaterow_cuenta_y_suma_con_su_tabla_de_operaciones():
    nodo = nodo_desde_plantilla(
        "tAggregateRow",
        "tAggregateRow_1",
        tablas={
            "OPERATIONS": (
                ("OUTPUT_COLUMN", "total_filas"), ("FUNCTION", "count"),
                ("INPUT_COLUMN", "valor"), ("IGNORE_NULL", "false"),
                ("OUTPUT_COLUMN", "suma_valor"), ("FUNCTION", "sum"),
                ("INPUT_COLUMN", "valor"), ("IGNORE_NULL", "false"),
            ),
        },
        columnas=[Columna("total_filas", "id_Long"), Columna("suma_valor", "id_Double")],
    )
    (xml_nodo,) = _xml([nodo]).findall("node")
    operaciones = _tabla(xml_nodo, "OPERATIONS")
    assert xml_nodo.get("componentName") == "tAggregateRow"
    assert operaciones[1] == ("FUNCTION", "count")
    assert operaciones[5] == ("FUNCTION", "sum")
    assert len(operaciones) == 8
    assert _tabla(xml_nodo, "GROUPBYS") == []
    assert _columnas(xml_nodo) == ["total_filas", "suma_valor"]


def test_tunite_une_dos_flujos_del_mismo_esquema_por_conexion_merge():
    origen_a = nodo_desde_plantilla("tFileInputExcel", "fuente_a", columnas=ENTRADA)
    origen_b = nodo_desde_plantilla("tFileInputExcel", "fuente_b", columnas=ENTRADA)
    unite = nodo_desde_plantilla("tUnite", "tUnite_1", columnas=ENTRADA)
    # FLOW_MERGE de EConnectionType de Studio: conector MERGE, lineStyle 10 (medido con javap).
    conexiones = [
        Conexion("fuente_a", "tUnite_1", "row1", "MERGE", 10),
        Conexion("fuente_b", "tUnite_1", "row2", "MERGE", 10),
    ]
    raiz = _xml([origen_a, origen_b, unite], conexiones)
    entradas = [c for c in raiz.findall("connection") if c.get("target") == "tUnite_1"]
    assert {c.get("connectorName") for c in entradas} == {"MERGE"}
    assert {c.get("lineStyle") for c in entradas} == {"10"}
    (xml_unite,) = [n for n in raiz.findall("node") if n.get("componentName") == "tUnite"]
    assert _columnas(xml_unite) == ["id", "nombre", "cantidad"]


def test_treplicate_envia_cada_fila_a_dos_destinos():
    origen = nodo_desde_plantilla("tReplicate", "tReplicate_1", columnas=ENTRADA)
    dos = [log_row(f"tLogRow_{i}", ENTRADA, x=300) for i in (1, 2)]
    conexiones = [
        Conexion("tReplicate_1", "tLogRow_1", "row1", "FLOW", 0),
        Conexion("tReplicate_1", "tLogRow_2", "row2", "FLOW", 0),
    ]
    raiz = _xml([origen, *dos], conexiones)
    salidas = [c.get("target") for c in raiz.findall("connection") if c.get("source") == "tReplicate_1"]
    assert salidas == ["tLogRow_1", "tLogRow_2"]
    (xml_rep,) = [n for n in raiz.findall("node") if n.get("componentName") == "tReplicate"]
    assert _columnas(xml_rep) == ["id", "nombre", "cantidad"]


def test_tfileexist_guarda_la_ruta_que_se_comprueba_y_su_condicion_run_if():
    comprueba = nodo_desde_plantilla(
        "tFileExist", "tFileExist_1", valores={"FILE_NAME": '"C:/datos/entrada.xlsx"'}
    )
    siguiente = nodo_desde_plantilla("tJava", "tJava_1", valores={"CODE": 'System.out.println("hay");'})
    conexion = si("tFileExist_1", "tJava_1", '((Boolean)globalMap.get("tFileExist_1_EXISTS"))')
    raiz = _xml([comprueba, siguiente], [conexion])
    (xml_nodo,) = [n for n in raiz.findall("node") if n.get("componentName") == "tFileExist"]
    assert _parametros(xml_nodo)["FILE_NAME"] == '"C:/datos/entrada.xlsx"'
    (run_if,) = raiz.findall("connection")
    assert run_if.get("connectorName") == "RUN_IF"
    assert run_if.get("lineStyle") == "6"
    assert run_if.find("elementParameter[@name='CONDITION']").get("value") == (
        '((Boolean)globalMap.get("tFileExist_1_EXISTS"))'
    )


def test_tsetglobalvar_fija_la_variable_con_su_tabla_variables():
    nodo = nodo_desde_plantilla(
        "tSetGlobalVar",
        "tSetGlobalVar_1",
        tablas={"VARIABLES": (("KEY", '"miVariable"'), ("VALUE", '"valor SGM"'))},
    )
    (xml_nodo,) = _xml([nodo]).findall("node")
    assert xml_nodo.get("componentName") == "tSetGlobalVar"
    assert _tabla(xml_nodo, "VARIABLES") == [("KEY", '"miVariable"'), ("VALUE", '"valor SGM"')]


def test_tlogcatcher_recoge_el_esquema_estandar_de_sus_mensajes():
    nodo = nodo_desde_plantilla("tLogCatcher", "tLogCatcher_1", columnas=CATCHER)
    (xml_nodo,) = _xml([nodo]).findall("node")
    params = _parametros(xml_nodo)
    assert xml_nodo.get("componentName") == "tLogCatcher"
    assert params["CATCH_TWARN"] == "true"
    assert params["CATCH_TDIE"] == "true"
    columnas = _columnas(xml_nodo)
    assert len(columnas) == 12
    assert {"root_pid", "message", "code", "origin"} <= set(columnas)
