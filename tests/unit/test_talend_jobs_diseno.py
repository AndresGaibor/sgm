"""Job padre del diseño de Talend: estructura, hijos referenciados y parámetros de producto."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.item import render_item, render_properties
from sgm.talend_item.jobs_diseno import ProductoJob, codigo_validar_entorno, job_padre
from sgm.talend_item.modelo import Job

DECISIONES = Path(__file__).resolve().parents[2] / "decisiones" / "client_large.jobs.yaml"
PRODUCTOS = [ProductoJob("cte", "", "cte"), ProductoJob("aho", "", "aho")]


@pytest.fixture(scope="module")
def arq():
    return cargar_arquitectura(DECISIONES)


def test_la_arquitectura_declarada_se_carga(arq):
    assert arq.padre == "job_exogena_depositos"
    assert arq.entornos == ("DEV", "QA", "PROD")
    assert arq.mensaje_fin == "Proceso terminado"


def test_una_arquitectura_sin_jobs_falla_con_el_motivo(tmp_path):
    archivo = tmp_path / "x.jobs.yaml"
    archivo.write_text("proyecto: P\nentornos: [DEV]\njobs: {padre: a}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="faltan los Jobs"):
        cargar_arquitectura(archivo)


def test_el_padre_recorre_insumos_productos_totales_y_conciliacion_en_orden(arq):
    raiz = ET.fromstring(render_item(job_padre(arq, PRODUCTOS)))
    hijos = [
        n.find("elementParameter[@name='PROCESS']").get("value")
        for n in raiz.findall("node")
        if n.get("componentName") == "tRunJob"
    ]
    assert hijos == ["job_insumos", "job_producto", "job_totales", "job_conciliacion"]
    tipos = [(c.get("connectorName"), c.get("source"), c.get("target")) for c in raiz.iter("connection")]
    assert ("SUBJOB_OK", "tRunJob_1", "tFixedFlowInput_1") in tipos
    assert ("SUBJOB_OK", "tFixedFlowInput_1", "tRunJob_3") in tipos
    assert ("SUBJOB_OK", "tRunJob_3", "tRunJob_4") in tipos
    assert ("ITERATE", "tFlowToIterate_1", "tRunJob_2") in tipos


def test_el_hijo_de_producto_recibe_producto_tabla_y_sufijo_del_flujo(arq):
    raiz = ET.fromstring(render_item(job_padre(arq, PRODUCTOS)))
    (run,) = [
        n
        for n in raiz.findall("node")
        if n.find("elementParameter[@name='UNIQUE_NAME']").get("value") == "tRunJob_2"
    ]
    celdas = run.findall("elementParameter[@name='CONTEXTPARAMS']/elementValue")
    pares = [(c.get("elementRef"), c.get("value")) for c in celdas]
    assert pares[0::2] == [("PARAM_NAME_COLUMN", n) for n in ("producto", "tabla_origen", "sufijo")]
    assert pares[1][1] == '(String) globalMap.get("row1.producto")'


def test_la_referencia_al_hijo_coincide_con_el_id_de_su_propiedad(arq):
    texto = render_item(job_padre(arq, PRODUCTOS))
    referencia = re.search(r'PROCESS:PROCESS_TYPE_PROCESS" value="PRJ_BANCOLOMBIA:(_[^"]+)"', texto)
    propiedades = render_properties(Job("job_insumos"), fecha="2026-11-04T00:00:00.000-0500")
    assert f'id="{referencia.group(1)}"' in propiedades


def test_las_filas_de_productos_salen_en_mayuscula_y_la_tabla_pendiente_queda_vacia(arq):
    raiz = ET.fromstring(render_item(job_padre(arq, PRODUCTOS)))
    valores = [
        v.get("value")
        for v in raiz.findall("node/elementParameter[@name='INTABLE']/elementValue")
    ]
    assert valores[:3] == ['"CTE"', '""', '"cte"']


def test_el_prejob_marca_el_entorno_y_un_tdie_condicionado_detiene_el_job(arq):
    codigo = codigo_validar_entorno(("DEV", "QA"))
    assert '"DEV", "QA"' in codigo and 'globalMap.put("env_valido"' in codigo
    raiz = ET.fromstring(render_item(job_padre(arq, PRODUCTOS)))
    (si_,) = [c for c in raiz.iter("connection") if c.get("connectorName") == "RUN_IF"]
    assert (si_.get("source"), si_.get("target")) == ("tJava_1", "tDie_1")
    assert "env_valido" in si_.find("elementParameter[@name='CONDITION']").get("value")
    assert si_.find("elementParameter[@name='ACTIVATE']") is None  # false = conexión desactivada


def test_el_comando_talend_escribe_el_job_padre_con_los_productos_declarados(tmp_path):
    from typer.testing import CliRunner

    from sgm.cli import app

    fuente = Path(__file__).resolve().parents[1] / "fixtures" / "sas" / "client" / "client_large.sas"
    resultado = CliRunner().invoke(app, ["talend", str(fuente), "--out", str(tmp_path)])
    assert resultado.exit_code == 0, resultado.output
    item = tmp_path / "client_large" / "talend" / "process" / "job_exogena_depositos_0.1.item"
    propiedades = item.with_suffix(".properties")
    assert item.exists() and propiedades.exists()
    valores = [
        v.get("value")
        for v in ET.parse(item).getroot().findall("node/elementParameter[@name='INTABLE']/elementValue")
    ]
    assert valores[:9:3] == ['"CTE"', '"AHO"', '"NEQUI"']
    assert "Pendiente: tabla de origen de 3 productos" in resultado.output
