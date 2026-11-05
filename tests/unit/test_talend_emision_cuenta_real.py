"""Hito 89 / R1-06 (parte 2): la forma del SAS real llega al `job_producto` emitido.

La cadena se comprueba sin Studio: `sgm talend` lee `client_large.sas`,
`reglas_cuenta_real` saca los dos `NOT BETWEEN` con `RELACION = 1000`, y el `.item` lleva una
cuarta rama del `tReplicate_1` con cuatro `expressionFilter`. La compilación y la ejecución con
datos quedan registradas en `PROGRESS.md`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest

from sgm.cli_talend import _cuenta, talend_command
from sgm.proceso.reglas_cuenta_real import MODOS, reglas_cuenta_real
from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.filtros_cuenta_real import ENTRADA, SALIDAS, filtros
from sgm.talend_item.flujos_cuenta_real import SALIDA, TMAP, componentes
from sgm.talend_item.item import render_item
from sgm.talend_item.jobs_producto import job_producto
from sgm.talend_item.modelo import Columna

RAIZ = Path(__file__).resolve().parents[2]
PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
DECISIONES = RAIZ / "decisiones" / "client_large.jobs.yaml"
TEXTO = PROGRAMA.read_text(encoding="utf-8", errors="replace")
CUENTA, PENDIENTES = reglas_cuenta_real(TEXTO)
COLS = [Columna(c) for c in CUENTA.columnas]
INFORMATS = {"GMF": (3, 0)}


@pytest.fixture(scope="module")
def item(tmp_path_factory) -> Path:
    salida = tmp_path_factory.mktemp("emision-hito89")
    talend_command(PROGRAMA, out=salida)
    archivo = salida / PROGRAMA.stem / "talend" / "process" / "job_producto_0.1.item"
    assert archivo.is_file()
    return archivo


def _raiz(item: Path) -> ET.Element:
    return ET.parse(item).getroot()


def _conexiones(raiz: ET.Element) -> list[tuple[str, str, str]]:
    return [(c.get("source"), c.get("target"), c.get("label")) for c in raiz.findall("connection")]


def _salidas(raiz: ET.Element) -> dict[str, ET.Element]:
    return {
        t.get("name"): t
        for t in raiz.iter("outputTables")
        if t.get("name") in SALIDAS.values()
    }


def test_el_item_emitido_cuelga_la_cuarta_rama_del_replicate(item):
    raiz = _raiz(item)
    nodo = next(
        (n for n in raiz.iter("node")
         if (p := n.find("elementParameter[@name='UNIQUE_NAME']")) is not None
         and p.get("value") == TMAP),
        None,
    )
    assert nodo is not None and nodo.get("componentName") == "tMap"
    conexiones = _conexiones(raiz)
    assert ("tReplicate_1", TMAP, ENTRADA) in conexiones
    assert ("tReplicate_1", "tMap_flujos", "flujos") in conexiones  # hito 87 sigue
    for n, modo in enumerate(MODOS, start=1):
        assert (TMAP, SALIDA.format(n=n), SALIDAS[modo]) in conexiones


def test_las_etiquetas_de_la_rama_no_chocan_con_las_anteriores(item):
    etiquetas = [c.get("label") for c in _raiz(item).findall("connection")]
    nuevas = [SALIDAS[m] for m in MODOS]
    # `row1`/`row2` ya se repetían antes del hito 89; aquí importa que los nombres de salida
    # del `tMap` sean únicos y no pisen `valido` (R1-04) ni la entrada `cuenta`.
    assert len(nuevas) == len(set(nuevas)) == 4
    assert all(etiquetas.count(nombre) == 1 for nombre in nuevas)
    assert "valido" in etiquetas and "flujos" in etiquetas
    assert ENTRADA not in nuevas and set(nuevas).isdisjoint({"tit_cot", "fa", "valido"})


def test_los_cuatro_filtros_del_item_son_los_del_sas_real(item):
    tablas = _salidas(_raiz(item))
    assert set(tablas) == set(SALIDAS.values())
    esperados = filtros(CUENTA, ENTRADA)
    for modo, nombre in SALIDAS.items():
        tabla = tablas[nombre]
        assert tabla.get("activateExpressionFilter") == "true"
        assert tabla.get("expressionFilter") == esperados[modo]
        assert "TIPO CTA INVALIDO" not in (tabla.get("expressionFilter") or "")
    assert '"1000".equals(cuenta.RELACION)' in tablas[SALIDAS["codex"]].get("expressionFilter")
    assert "cuenta.GMF.matches" in tablas[SALIDAS["codex"]].get("expressionFilter")


def test_las_proyecciones_del_item_salen_del_select_del_sas_real(item):
    tablas = _salidas(_raiz(item))
    for modo, nombre in SALIDAS.items():
        columnas = [e.get("name") for e in tablas[nombre].findall("mapperTableEntries")]
        esperado = (*CUENTA.columnas, "INCONSISTENCIA") if modo == "cuenta" else CUENTA.columnas
        assert columnas == list(esperado)
        assert columnas[0] == "RELACION"
        ultima = "INCONSISTENCIA" if modo == "cuenta" else "FIN_SALDO_CTA"
        assert columnas[-1] == ultima


def test_la_inconsistencia_del_item_usa_los_motivos_leidos_del_data_step(item):
    tablas = _salidas(_raiz(item))
    entradas = {
        e.get("name"): e.get("expression")
        for e in tablas[SALIDAS["cuenta"]].findall("mapperTableEntries")
    }
    motivo = entradas["INCONSISTENCIA"]
    assert '"TIPO CTA INVALIDO"' in motivo
    assert '"CODEX INVALIDO"' in motivo
    assert "GMF NO NUMERICO" not in motivo


def test_los_csv_usan_las_tablas_del_sas_y_el_sufijo(item):
    valores = [
        p.get("value")
        for p in _raiz(item).iter("elementParameter")
        if p.get("name") == "FILENAME"
    ]
    for modo in MODOS:
        esperado = (
            f'context.ruta_resultados + "{CUENTA.tablas[modo]}_" + context.sufijo + ".csv"'
        )
        assert esperado in valores


def test_el_contexto_del_item_declara_ruta_resultados(item):
    nombres = {p.get("name") for p in _raiz(item).iter("contextParameter")}
    assert "ruta_resultados" in nombres


def test_el_item_emitido_tiene_21_nodos(item):
    assert len(list(_raiz(item).iter("node"))) == 21


def test_sin_cuenta_el_job_no_emite_la_rama():
    arq = cargar_arquitectura(DECISIONES)
    raiz = ET.fromstring(render_item(job_producto(arq, ("A", "B", "FIN_SALDO_CTA"))))
    unicos = {
        p.get("value")
        for p in raiz.iter("elementParameter")
        if p.get("name") == "UNIQUE_NAME"
    }
    assert TMAP not in unicos
    assert not any(c.get("target") == TMAP for c in raiz.findall("connection"))


def test_componentes_exigen_la_normalizacion_de_gmf():
    with pytest.raises(ValueError, match="normalización de R1-02"):
        componentes(CUENTA, COLS, {})


def test_componentes_exigen_todas_las_columnas_proyectadas():
    with pytest.raises(ValueError, match="columnas que no se leen"):
        componentes(CUENTA, [Columna("RELACION")], INFORMATS)


def test_componentes_exigen_la_columna_de_control():
    columnas = [Columna(c) for c in CUENTA.columnas if c != "RELACION"]
    reglas = replace(CUENTA, columnas=tuple(c.nombre for c in columnas))
    with pytest.raises(ValueError, match="columna 'RELACION'"):
        componentes(reglas, columnas, INFORMATS)


def test_componentes_exigen_las_cuatro_tablas_del_sas():
    with pytest.raises(ValueError, match="tablas del SAS"):
        componentes(replace(CUENTA, tablas={"cuenta": "X"}), COLS, INFORMATS)


def test_componentes_exigen_una_proyeccion_no_vacia():
    with pytest.raises(ValueError, match="Sin proyección"):
        componentes(replace(CUENTA, columnas=()), COLS, INFORMATS)


def test_un_programa_sin_la_forma_real_no_emite_la_rama_a_medias():
    reglas, pendientes = _cuenta("PROC SQL; QUIT;")
    assert reglas is None
    assert any("no se emiten los flujos de cuenta y codex" in p for p in pendientes)


def test_las_reglas_fuera_de_la_cadena_se_publican_como_pendientes():
    reglas, pendientes = _cuenta(TEXTO)
    assert reglas == CUENTA
    assert len(pendientes) == 3
    assert any("OUTER UNION CORR" in p for p in pendientes)
    assert any("R1-07" in p for p in pendientes)
    assert PENDIENTES == pendientes
