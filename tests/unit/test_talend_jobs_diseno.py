"""Job padre del diseño de Talend: estructura, hijos referenciados, periodo y productos."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.cli import app
from sgm.proceso.insumos import resolver_insumos
from sgm.proceso.secciones_entrada import cargar_declaradas
from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.item import render_item, render_properties
from sgm.talend_item.jobs_diseno import (
    ProductoJob,
    codigo_validar_entorno,
    job_padre,
    jobs_hijos,
)
from sgm.talend_item.modelo import Job
from sgm.talend_item.periodo import contextos_de_periodo, nodos_periodo, nombre_columna

RAIZ = Path(__file__).resolve().parents[2]
DECISIONES = RAIZ / "decisiones" / "client_large.jobs.yaml"
PRODUCTOS = [ProductoJob("cte", "", "cte"), ProductoJob("aho", "", "aho")]


@pytest.fixture(scope="module")
def arq():
    return cargar_arquitectura(DECISIONES)


@pytest.fixture(scope="module")
def resueltos(arq):
    texto = (RAIZ / "tests/fixtures/sas/client/client_large.sas").read_text(
        encoding="utf-8", errors="replace"
    )
    declaradas = cargar_declaradas(RAIZ / "decisiones" / "client_large.diseno.yaml", "fuentes")
    return resolver_insumos(texto, declaradas, [*arq.lookups, arq.periodo.fuente])


@pytest.fixture(scope="module")
def padre(arq, resueltos):
    return job_padre(
        arq,
        PRODUCTOS,
        periodo=nodos_periodo(arq, resueltos),
        contextos_periodo=contextos_de_periodo(arq, resueltos),
    )


def _conexiones(job: Job) -> list[tuple[str, str, str]]:
    raiz = ET.fromstring(render_item(job))
    return [(c.get("connectorName"), c.get("source"), c.get("target")) for c in raiz.iter("connection")]


def test_la_arquitectura_declarada_se_carga(arq):
    assert arq.padre == "job_exogena_depositos"
    assert arq.entornos == ("DEV", "QA", "PROD")
    assert arq.mensaje_fin == "Proceso terminado"
    assert arq.periodo.fuente == "Validación de fecha"
    assert len(arq.lookups) == 4


def test_una_arquitectura_sin_jobs_falla_con_el_motivo(tmp_path):
    archivo = tmp_path / "x.jobs.yaml"
    archivo.write_text("proyecto: P\nentornos: [DEV]\njobs: {padre: a}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="faltan los Jobs"):
        cargar_arquitectura(archivo)


def test_un_periodo_sin_variables_falla_con_el_motivo(tmp_path):
    archivo = tmp_path / "x.jobs.yaml"
    archivo.write_text(
        "proyecto: P\nentornos: [DEV]\nmensaje_fin: x\n"
        "jobs: {padre: a, producto: c, totales: d, conciliacion: e}\n"
        "periodo: {fuente: F}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="`periodo` necesita"):
        cargar_arquitectura(archivo)


def test_el_padre_lee_el_periodo_y_recorre_productos_totales_y_conciliacion_en_orden(padre):
    raiz = ET.fromstring(render_item(padre))
    hijos = [
        n.find("elementParameter[@name='PROCESS']").get("value")
        for n in raiz.findall("node")
        if n.get("componentName") == "tRunJob"
    ]
    assert hijos == ["job_producto", "job_totales", "job_conciliacion"]
    tipos = _conexiones(padre)
    assert ("SUBJOB_OK", "tFileInputExcel_1", "tFixedFlowInput_1") in tipos
    assert ("SUBJOB_OK", "tFixedFlowInput_1", "tRunJob_2") in tipos
    assert ("SUBJOB_OK", "tRunJob_2", "tRunJob_3") in tipos
    assert ("ITERATE", "tFlowToIterate_1", "tRunJob_1") in tipos


def test_sin_periodo_resuelto_el_padre_arranca_en_los_productos(arq):
    raiz = ET.fromstring(render_item(job_padre(arq, PRODUCTOS)))
    assert "tFileInputExcel" not in [n.get("componentName") for n in raiz.findall("node")]


def test_el_periodo_se_lee_con_las_variables_de_contexto_y_deja_la_fecha_en_el_contexto(padre):
    raiz = ET.fromstring(render_item(padre))
    contexto = {c.get("name"): c.get("value") for c in raiz.findall("context/contextParameter")}
    assert contexto["arch_validacion_fecha"] == "Validacion_fecha.xlsx"
    assert contexto["hoja_excel"] == "Sheet1"
    assert {"periodo_anio", "periodo_mes", "periodo_dia"} <= set(contexto)
    (excel,) = [n for n in raiz.findall("node") if n.get("componentName") == "tFileInputExcel"]
    nombre = excel.find("elementParameter[@name='FILENAME']").get("value")
    assert nombre == "context.ruta_insumos + context.arch_validacion_fecha"
    (fila,) = [n for n in raiz.findall("node") if n.get("componentName") == "tJavaRow"]
    codigo = fila.find("elementParameter[@name='CODE']").get("value")
    assert "context.periodo_anio = String.valueOf(input_row.ANO);" in codigo


def test_los_nombres_de_columna_son_validos_en_java_y_no_se_repiten():
    usadas: set[str] = set()
    assert nombre_columna("AÑO", usadas) == "ANO"
    assert nombre_columna("CODIGO DIAN", usadas) == "CODIGO_DIAN"
    assert nombre_columna("codigo_dian", usadas) == "codigo_dian_2"
    assert nombre_columna("1er dato", usadas) == "c_1er_dato"
    assert nombre_columna("***", usadas) == "col"


def test_el_hijo_de_producto_recibe_producto_tabla_y_sufijo_del_flujo(padre):
    raiz = ET.fromstring(render_item(padre))
    (run,) = [
        n
        for n in raiz.findall("node")
        if n.find("elementParameter[@name='UNIQUE_NAME']").get("value") == "tRunJob_1"
    ]
    celdas = run.findall("elementParameter[@name='CONTEXTPARAMS']/elementValue")
    pares = [(c.get("elementRef"), c.get("value")) for c in celdas]
    assert pares[0::2] == [("PARAM_NAME_COLUMN", n) for n in ("producto", "tabla_origen", "sufijo")]
    assert pares[1][1] == '(String) globalMap.get("row1.producto")'


def test_los_hijos_heredan_e_imprimen_las_variables_del_periodo(arq):
    variables = tuple(v for _, v in arq.periodo.variables)
    hijos = {j.nombre: j for j in jobs_hijos(arq, variables)}
    assert list(hijos) == ["job_producto", "job_totales", "job_conciliacion"]
    raiz = ET.fromstring(render_item(hijos["job_totales"]))
    contexto = [c.get("name") for c in raiz.findall("context/contextParameter")]
    assert contexto == ["periodo_anio", "periodo_mes", "periodo_dia"]
    assert "context.periodo_mes" in raiz.find("node/elementParameter[@name='CODE']").get("value")


def test_la_referencia_al_hijo_coincide_con_el_id_de_su_propiedad(padre):
    texto = render_item(padre)
    referencia = re.search(r'PROCESS:PROCESS_TYPE_PROCESS" value="PRJ_BANCOLOMBIA:(_[^"]+)"', texto)
    propiedades = render_properties(Job("job_producto"), fecha="2026-11-04T00:00:00.000-0500")
    assert f'id="{referencia.group(1)}"' in propiedades


def test_las_filas_de_productos_salen_en_mayuscula_y_la_tabla_pendiente_queda_vacia(padre):
    raiz = ET.fromstring(render_item(padre))
    valores = [
        v.get("value") for v in raiz.findall("node/elementParameter[@name='INTABLE']/elementValue")
    ]
    assert valores[:3] == ['"CTE"', '""', '"cte"']


def test_el_prejob_marca_el_entorno_y_un_tdie_condicionado_detiene_el_job(padre):
    codigo = codigo_validar_entorno(("DEV", "QA"))
    assert '"DEV", "QA"' in codigo and 'globalMap.put("env_valido"' in codigo
    raiz = ET.fromstring(render_item(padre))
    (si_,) = [c for c in raiz.iter("connection") if c.get("connectorName") == "RUN_IF"]
    assert (si_.get("source"), si_.get("target")) == ("tJava_1", "tDie_1")
    assert "env_valido" in si_.find("elementParameter[@name='CONDITION']").get("value")
    assert si_.find("elementParameter[@name='ACTIVATE']") is None  # false = conexión desactivada


def test_el_comando_talend_escribe_el_padre_y_los_tres_hijos(tmp_path):
    fuente = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
    resultado = CliRunner().invoke(app, ["talend", str(fuente), "--out", str(tmp_path)])
    assert resultado.exit_code == 0, resultado.output
    carpeta = tmp_path / "client_large" / "talend" / "process"
    nombres = sorted(p.name for p in carpeta.glob("*.item"))
    assert nombres == [
        "job_conciliacion_0.1.item",
        "job_exogena_depositos_0.1.item",
        "job_producto_0.1.item",
        "job_totales_0.1.item",
    ]
    producto = ET.parse(carpeta / "job_producto_0.1.item").getroot()
    codigo = producto.find("node/elementParameter[@name='CODE']").get("value")
    assert "Cod_pais.xlsx (Codigo_Pais, Nombre Pais)" in codigo
    assert "Pendiente: tabla de origen de 3 productos" in resultado.output
