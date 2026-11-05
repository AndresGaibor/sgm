"""Hito 87 / R1-04 (parte 1): los tres flujos llegan al `job_producto` **emitido**.

La cadena completa se comprueba sin Studio: `sgm talend` lee `client_large.sas`,
`reglas_fila.flujos_producto` saca la terna canónica y su proyección del `SELECT`, y el `.item`
lleva un `tMap` con los tres `expressionFilter` que el hito 86 verificó fila por fila en Studio.
La compilación y la ejecución reales quedan registradas en `PROGRESS.md`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.cli_talend import _flujos, talend_command
from sgm.proceso.reglas_fila import flujos_producto
from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.filtros_fila import filtro
from sgm.talend_item.flujos_fila import ENTRADA, TMAP, componentes
from sgm.talend_item.item import render_item
from sgm.talend_item.jobs_producto import job_producto
from sgm.talend_item.modelo import Columna

RAIZ = Path(__file__).resolve().parents[2]
PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
V02 = RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v02_vacios_ceros" / "programa.sas"
DECISIONES = RAIZ / "decisiones" / "client_large.jobs.yaml"
TEXTO = PROGRAMA.read_text(encoding="utf-8", errors="replace")
FLUJOS, _ = flujos_producto(TEXTO)
INFORMATS = {"NRO_DOC": (30, 0)}


@pytest.fixture(scope="module")
def item(tmp_path_factory) -> Path:
    salida = tmp_path_factory.mktemp("emision-hito87")
    talend_command(PROGRAMA, out=salida)
    archivo = salida / PROGRAMA.stem / "talend" / "process" / "job_producto_0.1.item"
    assert archivo.is_file()
    return archivo


def _raiz(item: Path) -> ET.Element:
    return ET.parse(item).getroot()


def _nodo(raiz: ET.Element, nombre: str) -> ET.Element | None:
    for nodo in raiz.iter("node"):
        unico = nodo.find("elementParameter[@name='UNIQUE_NAME']")
        if unico is not None and unico.get("value") == nombre:
            return nodo
    return None


def _conexiones(raiz: ET.Element) -> list[tuple[str, str, str]]:
    return [(c.get("source"), c.get("target"), c.get("label")) for c in raiz.findall("connection")]


def test_el_item_emitido_cuelga_los_tres_flujos_como_tercera_rama_del_replicate(item):
    raiz = _raiz(item)
    nodo = _nodo(raiz, TMAP)
    assert nodo is not None and nodo.get("componentName") == "tMap"
    conexiones = _conexiones(raiz)
    assert ("tReplicate_1", TMAP, ENTRADA) in conexiones
    assert ("tReplicate_1", "tMap_1", "row1") in conexiones  # las ramas del hito 84 siguen
    assert ("tReplicate_1", "tMap_2", "copy2") in conexiones
    for n, modo in enumerate(("tit_cot", "fa", "valido"), start=1):
        assert (TMAP, f"tFileOutputDelimited_flujos_{n}", modo) in conexiones


def test_los_tres_filtros_del_item_son_los_verificados_en_el_hito_86(item):
    tablas = {
        t.get("name"): t
        for t in _raiz(item).iter("outputTables")
        if t.get("name") in ("tit_cot", "fa", "valido")
    }
    assert set(tablas) == {"tit_cot", "fa", "valido"}
    for flujo in FLUJOS:
        tabla = tablas[flujo.modo]
        assert tabla.get("activateExpressionFilter") == "true"
        assert tabla.get("expressionFilter") == filtro(flujo, ENTRADA)
        assert "flujos.NRO_DOC.equals" not in tabla.get("expressionFilter", "")
    assert '!"9902".equals(flujos.RELACION)' in tablas["tit_cot"].get("expressionFilter", "")
    assert '"9902".equals(flujos.RELACION)' in tablas["fa"].get("expressionFilter", "")


def test_las_proyecciones_del_item_salen_del_select_del_sas_real(item):
    tablas = {
        t.get("name"): [e.get("name") for e in t.findall("mapperTableEntries")]
        for t in _raiz(item).iter("outputTables")
        if t.get("name") in ("tit_cot", "fa", "valido")
    }
    for flujo in FLUJOS:
        assert tablas[flujo.modo] == list(flujo.columnas)
        assert len(tablas[flujo.modo]) == 19
        assert tablas[flujo.modo][0] == "RELACION"
        assert tablas[flujo.modo][-1] == "FIN_SALDO_CTA"


def test_los_csv_usan_el_nombre_de_la_tabla_del_sas_y_el_sufijo(item):
    valores = [
        p.get("value")
        for p in _raiz(item).iter("elementParameter")
        if p.get("name") == "FILENAME" and "NRO_DOC" in (p.get("value") or "")
    ]
    assert len(valores) == 3
    for flujo in FLUJOS:
        esperado = (
            f'context.ruta_resultados + "{flujo.tabla}_" + context.sufijo + ".csv"'
        )
        assert esperado in valores


def test_el_contexto_del_item_declara_ruta_resultados(item):
    nombres = {p.get("name") for p in _raiz(item).iter("contextParameter")}
    assert "ruta_resultados" in nombres


def test_el_item_emitido_tiene_21_nodos(item):
    # 16 del hito 87 + tMap_cuenta y sus 4 salidas del hito 89.
    assert len(list(_raiz(item).iter("node"))) == 21


def test_sin_flujos_el_job_queda_como_en_el_hito_84():
    arq = cargar_arquitectura(DECISIONES)
    raiz = ET.fromstring(render_item(job_producto(arq, ("A", "B", "FIN_SALDO_CTA"))))
    assert _nodo(raiz, TMAP) is None
    assert not any(c.get("target") == TMAP for c in raiz.findall("connection"))


def test_los_flujos_exigen_la_normalizacion_de_la_columna_filtrada():
    cols = [Columna(c) for c in FLUJOS[0].columnas]
    with pytest.raises(ValueError, match="normalización de R1-02"):
        componentes(FLUJOS, cols, {})


def test_no_se_emite_un_flujo_cuya_proyeccion_no_se_lee():
    with pytest.raises(ValueError, match="columnas que no se leen"):
        componentes(FLUJOS, [Columna("NRO_DOC")], INFORMATS)


def test_no_se_emite_una_terna_incompleta():
    cols = [Columna(c) for c in FLUJOS[0].columnas]
    with pytest.raises(ValueError, match="exactamente"):
        componentes(FLUJOS[:2], cols, INFORMATS)


def test_un_programa_sin_r1_04_no_emite_flujos_a_medias():
    flujos, pendientes = _flujos("PROC SQL; QUIT;")
    assert flujos == []
    assert any("no se emiten flujos" in p for p in pendientes)


def test_la_terna_de_v02_sirve_para_el_mismo_emisor():
    """El caso del corpus proyecta 6/6/7 columnas; el emisor no impone las 19 del SAS real."""
    corpus, _ = flujos_producto(V02.read_text(encoding="utf-8", errors="replace"))
    cols = [Columna(c) for c in ("RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE",
                                 "TIPO_DOC", "NRO_DOC", "FIN_SALDO_CTA")]
    nodos, conexiones = componentes(corpus, cols, INFORMATS)
    assert len(nodos) == 4 and len(conexiones) == 4
    conteo = {m.nombre: len(m.columnas) for m in nodos[0].metadatas}
    assert [conteo[f.modo] for f in corpus] == [6, 6, 7]
