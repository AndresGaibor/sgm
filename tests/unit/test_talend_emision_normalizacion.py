"""Hito 84 / R1-02 (parte 2): la normalización llega al `.item` que emite `sgm talend`.

Las expresiones sueltas ya se verificaron en Studio (hito 83). Aquí se comprueba la cadena completa
sin Studio: el SAS real declara los informats `w.d`, `esquema_csv` los lee, `origenes_producto` los
reúne, `cli_talend` los pasa y `job_producto` escribe un `tMap_normalizacion` conectado. La
compilación real del Job emitido queda registrada en `PROGRESS.md` (hito 84).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.cli_talend import talend_command
from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.item import render_item
from sgm.talend_item.jobs_producto import job_producto

RAIZ = Path(__file__).resolve().parents[2]
PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
DECISIONES = RAIZ / "decisiones" / "client_large.jobs.yaml"


@pytest.fixture(scope="module")
def arq():
    return cargar_arquitectura(DECISIONES)


@pytest.fixture(scope="module")
def item_emitido(tmp_path_factory) -> Path:
    """Emite los Jobs del SAS real con `sgm talend` y devuelve el `.item` de producto."""
    salida = tmp_path_factory.mktemp("emision-hito84")
    talend_command(PROGRAMA, out=salida)
    archivo = salida / PROGRAMA.stem / "talend" / "process" / "job_producto_0.1.item"
    assert archivo.is_file()
    return archivo


def _nodo(raiz: ET.Element, nombre: str) -> ET.Element | None:
    for nodo in raiz.iter("node"):
        unico = nodo.find("elementParameter[@name='UNIQUE_NAME']")
        if unico is not None and unico.get("value") == nombre:
            return nodo
    return None


def _expresiones(nodo: ET.Element) -> dict[str, str]:
    """Expresiones no vacías del `tMap`: nombre de columna -> expresión Java."""
    return {
        e.get("name"): e.get("expression")
        for e in nodo.iter("mapperTableEntries")
        if e.get("expression")
    }


def _conexiones(raiz: ET.Element) -> list[tuple[str, str, str]]:
    return [
        (c.get("source"), c.get("target"), c.get("label"))
        for c in raiz.findall("connection")
    ]


def test_el_item_emitido_lleva_un_tmap_de_normalizacion_entre_la_lectura_y_el_replicate(item_emitido):
    raiz = ET.parse(item_emitido).getroot()

    nodo = _nodo(raiz, "tMap_normalizacion")
    assert nodo is not None
    assert nodo.get("componentName") == "tMap"
    conexiones = _conexiones(raiz)
    assert ("tFileInputDelimited_1", "tMap_normalizacion", "row1") in conexiones
    assert ("tMap_normalizacion", "tReplicate_1", "normalizados") in conexiones
    assert ("tFileInputDelimited_1", "tReplicate_1", "row1") not in conexiones


def test_el_tmap_normaliza_solo_las_15_columnas_que_el_sas_declara_numericas(item_emitido):
    nodo = _nodo(ET.parse(item_emitido).getroot(), "tMap_normalizacion")
    expresiones = _expresiones(nodo)

    assert len(expresiones) == 23  # el esquema completo se conserva
    convertidas = {n for n, e in expresiones.items() if "java.util.Objects.toString" in e}
    assert len(convertidas) == 15
    assert {"NRO_CTA", "TIPO_DOC", "GMF", "FIN_SALDO_CTA"} <= convertidas
    for nombre, expresion in expresiones.items():
        assert nombre in expresion, f"{nombre}: la expresión no lee su columna"
        if nombre not in convertidas:
            assert expresion == f"row1.{nombre}"


def test_los_anchos_del_item_son_los_informats_reales_del_sas(item_emitido):
    nodo = _nodo(ET.parse(item_emitido).getroot(), "tMap_normalizacion")
    expresiones = _expresiones(nodo)

    assert "substring(0, 30)" in expresiones["NRO_CTA"]
    assert "substring(0, 8)" in expresiones["TIPO_DOC"]
    assert "substring(0, 3)" in expresiones["GMF"]
    assert "substring(0, 30)" in expresiones["FIN_SALDO_CTA"]
    assert "new java.math.BigDecimal(" in expresiones["TIPO_DOC"]
    assert "movePointLeft(0)" in expresiones["TIPO_DOC"]
    assert expresiones["ANIO_PROCESO"] == "row1.ANIO_PROCESO"


def test_sin_numericas_el_job_no_emite_normalizacion_ni_cambia_las_conexiones(arq):
    job = job_producto(arq, ("A", "B", "FIN_SALDO_CTA"))
    raiz = ET.fromstring(render_item(job))

    assert _nodo(raiz, "tMap_normalizacion") is None
    assert ("tFileInputDelimited_1", "tReplicate_1", "row1") in _conexiones(raiz)


def test_con_numericas_el_saldo_y_los_validos_usan_el_mismo_informat(arq):
    from sgm.talend_item.arquitectura import ValidacionProducto

    validacion = ValidacionProducto(
        "tipo_documento", "TIPO_DOC", "CNAME", "TIPO_DOC_INVALIDO", "Homologación", ()
    )
    job = job_producto(
        arq,
        ("A", "B", "FIN_SALDO_CTA"),
        validacion=validacion,
        numericas={"FIN_SALDO_CTA": (30, 0), "A": (8, 2)},
    )

    texto = render_item(job)
    raiz = ET.fromstring(texto)
    nodo = _nodo(raiz, "tMap_normalizacion")
    assert nodo is not None
    assert ("tFileInputDelimited_1", "tMap_normalizacion", "row1") in _conexiones(raiz)

    normalizadas = _expresiones(nodo)
    assert "substring(0, 30)" in normalizadas["FIN_SALDO_CTA"]
    assert "movePointLeft(2)" in normalizadas["A"]  # informat 8.2, no el 20 por omisión
    saldos = [
        e.get("expression") or ""
        for e in raiz.iter("mapperTableEntries")
        if "BigDecimal" in (e.get("expression") or "") and "FIN_SALDO_CTA" in (e.get("expression") or "")
    ]
    # normalización, totales de origen y filas válidas comparten el informat real
    assert len(saldos) >= 2
    assert all("substring(0, 30)" in e for e in saldos)
