"""`job_producto` con totales (R2-02, parte 2): escribe lo que lee `job_totales`.

Los archivos tienen el esquema de `jobs_totales.COLUMNAS_TOTALES`, con los nombres
`totales_origen_<sufijo>.csv` y `totales_salida_<sufijo>.csv` en la carpeta de resultados.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.talend_item.arquitectura import ValidacionProducto, cargar_arquitectura
from sgm.talend_item.item import render_item
from sgm.talend_item.jobs_producto import job_producto
from sgm.talend_item.jobs_totales import COLUMNAS_TOTALES

RAIZ = Path(__file__).resolve().parents[2]
DECISIONES = RAIZ / "decisiones" / "client_large.jobs.yaml"
VALIDACION = ValidacionProducto(
    "tipo_documento",
    "TIPO_DOC",
    "CNAME",
    "TIPO_DOC_INVALIDO",
    "Homologación de tipo de documento",
    (("NEQUI", "Homologación de tipo de documento Nequi"),),
)
COLUMNAS = ("LLAVE", "TIPO_DOC", "FIN_SALDO_CTA")


@pytest.fixture(scope="module")
def arq():
    return cargar_arquitectura(DECISIONES)


def _filenames(job) -> list[str]:
    """`FILENAME` de cada `tFileOutputDelimited` del Job."""
    raiz = ET.fromstring(render_item(job))
    nombres = []
    for nodo in raiz.iter("node"):
        if nodo.get("componentName") != "tFileOutputDelimited":
            continue
        for parametro in nodo.iter("elementParameter"):
            if parametro.get("name") == "FILENAME":
                nombres.append(parametro.get("value") or "")
    return nombres


def test_con_totales_el_job_escribe_origen_y_salida_con_el_sufijo(arq):
    job = job_producto(arq, COLUMNAS, validacion=VALIDACION, escribe_totales=True)

    archivos = _filenames(job)
    assert any("totales_origen_" in f and "context.sufijo" in f for f in archivos)
    assert any("totales_salida_" in f and "context.sufijo" in f for f in archivos)
    assert all("context.ruta_resultados" in f for f in archivos if "totales_" in f)


def test_sin_totales_el_job_queda_como_antes(arq):
    job = job_producto(arq, COLUMNAS, validacion=VALIDACION)

    texto = render_item(job)
    assert "totales_origen_" not in texto
    assert "totales_salida_" not in texto


def test_el_esquema_de_los_archivos_es_el_que_lee_job_totales(arq):
    job = job_producto(arq, COLUMNAS, validacion=VALIDACION, escribe_totales=True)

    texto = render_item(job).replace("&quot;", '"')
    for columna in COLUMNAS_TOTALES:
        assert columna.nombre in texto
    assert '"origen"' in texto
    assert '"salida"' in texto


def test_el_conteo_de_saldos_no_vacios_del_origen_se_suma_con_nulos_ignorados(arq):
    job = job_producto(arq, COLUMNAS, validacion=VALIDACION, escribe_totales=True)

    texto = render_item(job)
    assert "saldos_origen" in texto
    assert "suma_saldo_origen" in texto
    assert "row_tot_o.saldos_origen" in texto.replace("&quot;", '"')


def test_la_suma_nula_se_escribe_vacia_y_no_como_cero(arq):
    job = job_producto(arq, COLUMNAS, validacion=VALIDACION, escribe_totales=True)

    texto = render_item(job).replace("&quot;", '"')
    assert "row_tot_o.suma_saldo_origen == null" in texto
    assert "row_tot_s.suma_saldo_valido == null" in texto
    assert "toPlainString()" in texto


def test_sin_validacion_no_hay_salida_de_totales(arq):
    with pytest.raises(ValueError, match="validación de producto"):
        job_producto(arq, COLUMNAS, escribe_totales=True)


def test_sin_columna_de_saldo_no_hay_totales(arq):
    with pytest.raises(ValueError, match="columna de saldo"):
        job_producto(arq, ("LLAVE", "TIPO_DOC"), validacion=VALIDACION, escribe_totales=True)


def test_cada_agregado_tiene_una_sola_salida_principal(arq):
    """Un agregado con dos conexiones principales llegaba sin valores en Studio (v100a, v100b)."""
    job = job_producto(arq, COLUMNAS, validacion=VALIDACION, escribe_totales=True)

    raiz = ET.fromstring(render_item(job))
    origenes = [
        c.get("source") for c in raiz.findall("connection") if c.get("connectorName") == "FLOW"
    ]
    for agregado in ("tAggregateRow_1", "tAggregateRow_2"):
        assert origenes.count(agregado) == 1
