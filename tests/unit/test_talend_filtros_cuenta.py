"""Hito 88: los `expressionFilter` de cuenta y GMF son nulo-seguros y fieles al faltante de SAS."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas_cuenta import reglas_cuenta
from sgm.talend_item.filtros_cuenta import (
    MODOS,
    en_lista,
    faltante,
    fuera_de_rango,
    inconsistencia,
    motivo_gmf,
    salidas,
)

CASO = (
    Path(__file__).resolve().parents[2]
    / "tests" / "corpus" / "L8" / "validaciones" / "v04_tipo_cta_gmf"
)


@pytest.fixture(scope="module")
def reglas():
    return reglas_cuenta((CASO / "programa.sas").read_text(encoding="utf-8"))


def test_la_lista_lleva_el_literal_a_la_izquierda_y_es_nulo_segura():
    expr = en_lista("TIPO_CTA", ("1", "2"))

    assert expr == '("1".equals(row1.TIPO_CTA) || "2".equals(row1.TIPO_CTA))'
    assert "row1.TIPO_CTA.equals" not in expr


def test_una_lista_vacia_no_se_traduce():
    with pytest.raises(ValueError, match="no puede estar vacía"):
        en_lista("TIPO_CTA", ())


def test_el_faltante_comprueba_nulo_vacio_y_texto_no_numerico_antes_de_parsear():
    expr = faltante("GMF", "sabana")

    assert expr.startswith("(sabana.GMF == null || \"\".equals(sabana.GMF)")
    assert "|| !sabana.GMF.matches(" in expr
    assert "parseDouble" not in expr


def test_el_rango_incluye_al_faltante_como_menor_que_cualquier_numero(reglas):
    expr = fuera_de_rango(reglas.columna_rango, reglas.desde, reglas.hasta, "sabana")

    assert expr.startswith("((sabana.GMF == null")
    assert "java.lang.Double.parseDouble(sabana.GMF) < 1" in expr
    assert "java.lang.Double.parseDouble(sabana.GMF) > 10" in expr
    # Los límites salen del SAS, no están repetidos a mano en el traductor.
    assert expr == fuera_de_rango("GMF", 1, 10, "sabana")


def test_un_rango_invertido_no_se_emite():
    with pytest.raises(ValueError, match="invertido"):
        fuera_de_rango("GMF", 10, 1)


def test_el_motivo_del_gmf_distingue_faltante_de_fuera_de_rango(reglas):
    expr = motivo_gmf(reglas, "sabana")

    assert expr.startswith("(") and " ? " in expr and " : " in expr
    assert '"GMF NO NUMERICO"' in expr
    assert '"GMF FUERA DE RANGO"' in expr
    assert ";" not in expr


def test_la_inconsistencia_primero_mira_el_tipo_de_cuenta(reglas):
    expr = inconsistencia(reglas, "sabana")

    assert expr.startswith('(!("1".equals(sabana.TIPO_CTA)')
    assert '"TIPO CTA INVALIDO"' in expr
    assert '"GMF NO NUMERICO"' in expr


def test_las_cuatro_salidas_tienen_filtro_y_las_columnas_del_sas(reglas):
    obtenidas = salidas(reglas, "sabana")

    assert [s.nombre for s in obtenidas] == list(MODOS)
    assert all(s.filtro for s in obtenidas)
    for modo, salida in zip(MODOS, obtenidas, strict=True):
        assert [c.nombre for c in salida.columnas] == list(reglas.proyecciones[modo])
        assert set(salida.expresiones) == set(reglas.proyecciones[modo])


def test_los_filtros_de_las_salidas_son_los_de_las_reglas(reglas):
    obtenidas = {s.nombre: s.filtro for s in salidas(reglas, "sabana")}
    dentro = en_lista(reglas.columna_lista, reglas.valores, "sabana")
    fuera = fuera_de_rango(reglas.columna_rango, reglas.desde, reglas.hasta, "sabana")

    assert obtenidas == {
        "tipo_cta": f"!{dentro}",
        "gmf": f"({dentro} && {fuera})",
        "valido": f"({dentro} && !{fuera})",
        "cuenta": f"(!{dentro} || {fuera})",
    }


def test_el_item_lleva_los_cuatro_filtros_escapados_como_xml(reglas):
    from sgm.talend_item.modelo import Columna
    from sgm.talend_item.tmap import EntradaMap, tmap

    columnas = [Columna(c) for c in reglas.alias]
    nodo = tmap("tMap_filtros", [EntradaMap("sabana", columnas)], salidas(reglas, "sabana"))
    xml = nodo.datos

    assert xml.count('activateExpressionFilter="true"') == 4
    assert "&amp;&amp;" in xml
    assert "&lt; 1" in xml
    assert "&quot;GMF NO NUMERICO&quot;" in xml
