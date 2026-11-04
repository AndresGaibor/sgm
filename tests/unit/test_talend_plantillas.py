"""Plantillas de componentes de Talend: extracción neutra, instanciación y conexiones."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from sgm.talend_item.conexiones import al_terminar_componente, al_terminar_subjob, iterar, si
from sgm.talend_item.extraccion import UNICO, plantilla_desde_nodo
from sgm.talend_item.item import render_item
from sgm.talend_item.modelo import Columna, Job
from sgm.talend_item.plantillas import cargar, disponibles, nodo_desde_plantilla

COLUMNAS = [Columna("id", "id_Integer"), Columna("ciudad", "id_String")]
NODO_REAL = """
<node componentName="tJava" componentVersion="0.101" posX="10" posY="20">
  <elementParameter field="TEXT" name="UNIQUE_NAME" value="tJava_7" show="false"/>
  <elementParameter field="TEXT" name="LABEL" value="Mi etiqueta tJava_7"/>
  <elementParameter field="PASSWORD" name="PASSWORD" value="secreto"/>
  <elementParameter field="TEXT" name="HOST" value="servidor.interno"/>
  <elementParameter field="MEMO_EDITOR_JAVA" name="CODE" value="System.out.println(1);"/>
  <elementParameter field="TEXT" name="OTRO" value="conserva tJava_7"/>
  <elementParameter field="TABLE" name="TRIMSELECT">
    <elementValue elementRef="SCHEMA_COLUMN" value="a" id="0"/>
    <elementValue elementRef="TRIM" value="false" id="1"/>
    <elementValue elementRef="SCHEMA_COLUMN" value="b" id="2"/>
    <elementValue elementRef="TRIM" value="false" id="3"/>
  </elementParameter>
  <metadata connector="FLOW" name="tJava_7">
    <column name="a" type="id_String" key="false" nullable="true" length="-1" precision="-1"/>
    <column name="b" type="id_String" key="false" nullable="true" length="-1" precision="-1"/>
  </metadata>
  <metadata connector="REJECT" name="REJECT">
    <column name="a" type="id_String" key="false" nullable="true" length="-1" precision="-1"/>
    <column name="b" type="id_String" key="false" nullable="true" length="-1" precision="-1"/>
    <column name="errorMessage" type="id_String" key="false" nullable="true" length="255"
            precision="-1"/>
  </metadata>
</node>
"""


def _valores(plantilla: dict) -> dict[str, str | None]:
    return {f[1]: f[2] for f in plantilla["parametros"] if not isinstance(f, dict)}


def test_la_extraccion_neutraliza_lo_que_es_del_job_de_origen():
    plantilla = plantilla_desde_nodo(ET.fromstring(NODO_REAL))
    valores = _valores(plantilla)
    assert valores["UNIQUE_NAME"] == UNICO
    assert valores["PASSWORD"] == ""
    assert valores["HOST"] == ""
    assert valores["CODE"] == ""
    assert valores["LABEL"] == "__UNIQUE_NAME__"
    assert valores["OTRO"] == f"conserva {UNICO}"
    flow, reject = plantilla["metadatas"]
    assert flow["columnas"] == []
    assert reject["refleja_flow"] and [c["nombre"] for c in reject["columnas"]] == ["errorMessage"]


def test_las_tablas_por_columna_se_regeneran_con_el_esquema_pedido():
    plantilla = plantilla_desde_nodo(ET.fromstring(NODO_REAL))
    (tabla,) = [f for f in plantilla["parametros"] if isinstance(f, dict)]
    assert tabla["por_columna"] == [["TRIM", "false"]]


@pytest.mark.parametrize("componente", disponibles())
def test_cada_plantilla_instancia_y_se_escribe_como_xml_valido(componente):
    nodo = nodo_desde_plantilla(componente, f"{componente}_3", 100, 200, columnas=COLUMNAS)
    raiz = ET.fromstring(render_item(Job("Prueba", nodos=[nodo])))
    (xml_nodo,) = raiz.findall("node")
    nombres = {p.get("name"): p.get("value") for p in xml_nodo.findall("elementParameter")}
    assert nombres["UNIQUE_NAME"] == f"{componente}_3"
    assert "@@" not in render_item(Job("Prueba", nodos=[nodo]))


@pytest.mark.parametrize("componente", disponibles())
def test_ninguna_plantilla_guarda_contrasenas_ni_datos_de_otro_job(componente):
    for fila in cargar(componente)["parametros"]:
        if isinstance(fila, dict):
            continue
        campo, nombre, valor, _ = fila
        if campo == "PASSWORD" or nombre in {"USER", "HOST", "DBNAME", "FILENAME"}:
            assert not valor, f"{componente}.{nombre} trae un valor"
        if nombre in {"CODE", "QUERY", "MESSAGE", "PROCESS"}:
            assert valor in ("", '""'), f"{componente}.{nombre} trae un valor"


def test_el_lector_de_archivos_regenera_sus_tablas_y_el_rechazo_con_las_columnas():
    nodo = nodo_desde_plantilla(
        "tFileInputDelimited",
        "tFileInputDelimited_1",
        valores={"FILENAME": '"C:/datos/entrada.csv"', "HEADER": "1"},
        columnas=COLUMNAS,
    )
    tablas = {p.nombre: p for p in nodo.parametros if hasattr(p, "celdas")}
    assert [r for r, _ in tablas["TRIMSELECT"].celdas].count("SCHEMA_COLUMN") == 2
    assert [v for r, v in tablas["TRIMSELECT"].celdas if r == "SCHEMA_COLUMN"] == ["id", "ciudad"]
    flow, reject = nodo.metadatas
    assert [c.nombre for c in flow.columnas] == ["id", "ciudad"]
    assert [c.nombre for c in reject.columnas][:2] == ["id", "ciudad"]
    assert [c.nombre for c in reject.columnas][2:] == ["errorCode", "errorMessage"]


def test_un_parametro_que_el_componente_no_tiene_se_rechaza():
    with pytest.raises(KeyError, match="NO_EXISTE"):
        nodo_desde_plantilla("tJava", "tJava_1", valores={"NO_EXISTE": "1"})
    with pytest.raises(KeyError, match="plantilla"):
        nodo_desde_plantilla("tNoExiste", "tNoExiste_1")


def test_las_conexiones_de_disparo_iteracion_y_run_if_siguen_el_formato_de_studio():
    job = Job("Prueba", nodos=[], conexiones=[])
    job.conexiones += [
        al_terminar_subjob("a", "b", 2),
        al_terminar_componente("a", "c"),
        iterar("a", "d"),
        si("a", "e", 'globalMap.get("x") != null'),
    ]
    raiz = ET.fromstring(render_item(job))
    por_tipo = {c.get("connectorName"): c for c in raiz.findall("connection")}
    assert por_tipo["SUBJOB_OK"].get("lineStyle") == "1"
    assert por_tipo["SUBJOB_OK"].get("label") == "OnSubjobOk"
    assert por_tipo["SUBJOB_OK"].find("elementParameter").get("value") == "OnSubjobOk2"
    assert por_tipo["COMPONENT_OK"].get("lineStyle") == "3"
    assert por_tipo["ITERATE"].get("lineStyle") == "7"
    assert por_tipo["RUN_IF"].get("lineStyle") == "6"
    condicion = por_tipo["RUN_IF"].find("elementParameter[@name='CONDITION']")
    assert condicion.get("value") == 'globalMap.get("x") != null'


def test_los_saltos_de_linea_en_atributos_se_escriben_como_referencias():
    nodo = nodo_desde_plantilla("tJava", "tJava_1", valores={"CODE": "a();\n\tb();"})
    texto = render_item(Job("Prueba", nodos=[nodo]))
    assert 'value="a();&#10;&#09;b();"' in texto
    assert ET.fromstring(texto).find("node/elementParameter[@name='CODE']").get("value") == (
        "a();\n\tb();"
    )
