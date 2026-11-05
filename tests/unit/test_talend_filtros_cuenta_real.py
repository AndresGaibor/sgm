"""Hito 89: los cuatro `expressionFilter` de cuenta/codex son nulo-seguros y respetan la cascada."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from sgm.proceso.reglas_cuenta_real import MODOS, reglas_cuenta_real
from sgm.talend_item.filtros_cuenta_real import (
    ENTRADA,
    SALIDAS,
    control,
    filtros,
    fuera,
    inconsistencia,
    rechazo_codex,
    rechazo_tipo_cta,
    salidas,
)
from sgm.talend_item.modelo import Columna
from sgm.talend_item.tmap import EntradaMap, tmap

PROGRAMA = (
    Path(__file__).resolve().parents[2]
    / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
)


@pytest.fixture(scope="module")
def reglas():
    return reglas_cuenta_real(PROGRAMA.read_text(encoding="utf-8", errors="replace"))[0]


def test_el_control_lleva_el_literal_a_la_izquierda_y_es_nulo_seguro(reglas):
    expr = control(reglas)
    assert expr == '"1000".equals(cuenta.RELACION)'
    assert "cuenta.RELACION.equals" not in expr


def test_el_rango_cortocircuita_el_faltante_antes_de_parsear(reglas):
    expr = fuera(reglas.tipo_cta)
    assert expr.startswith("((cuenta.TIPO_CTA == null")
    assert "|| !cuenta.TIPO_CTA.matches(" in expr
    assert "java.lang.Double.parseDouble(cuenta.TIPO_CTA) < 1" in expr
    assert "java.lang.Double.parseDouble(cuenta.TIPO_CTA) > 5" in expr
    assert expr.index("matches(") < expr.index("parseDouble")


def test_el_primer_rechazo_exige_el_control_de_relacion(reglas):
    expr = rechazo_tipo_cta(reglas)
    assert expr.startswith('("1000".equals(cuenta.RELACION) && ')
    assert "cuenta.TIPO_CTA" in expr
    assert "cuenta.GMF" not in expr


def test_el_segundo_rechazo_respeta_la_cascada_y_la_exencion(reglas):
    expr = rechazo_codex(reglas)
    # El SAS evalúa el codex sobre SABANA_TIPO_CTA_VALIDO_*: niega el primer rechazo.
    assert expr.startswith(f"(!{rechazo_tipo_cta(reglas)}")
    assert '"1000".equals(cuenta.RELACION)' in expr
    assert "cuenta.GMF" in expr
    assert ";" not in expr


def test_los_cuatro_filtros_son_dos_rechazos_complemento_y_union(reglas):
    a = rechazo_tipo_cta(reglas)
    b = rechazo_codex(reglas)
    assert filtros(reglas) == {
        "tipo_cta": a,
        "codex": b,
        "valido": f"!({a} || {b})",
        "cuenta": f"({a} || {b})",
    }


def test_la_inconsistencia_prioriza_el_tipo_de_cuenta_con_los_motivos_del_sas(reglas):
    expr = inconsistencia(reglas)
    assert expr.startswith(f"({rechazo_tipo_cta(reglas)} ? ")
    assert '"TIPO CTA INVALIDO"' in expr
    assert '"CODEX INVALIDO"' in expr
    assert "GMF NO NUMERICO" not in expr
    assert ";" not in expr


def test_las_salidas_tienen_los_nombres_distintos_y_las_columnas_del_sas(reglas):
    obtenidas = salidas(reglas)
    assert [s.nombre for s in obtenidas] == [SALIDAS[m] for m in MODOS]
    assert len({s.nombre for s in obtenidas}) == 4
    assert ENTRADA not in {s.nombre for s in obtenidas}
    assert "valido" not in {s.nombre for s in obtenidas}  # ya lo usa la rama de R1-04
    for modo, salida in zip(MODOS, obtenidas, strict=True):
        columnas = (*reglas.columnas, "INCONSISTENCIA") if modo == "cuenta" else reglas.columnas
        assert [c.nombre for c in salida.columnas] == list(columnas)
        assert set(salida.expresiones) == set(columnas)
        assert salida.filtro == filtros(reglas)[modo]


def test_el_item_lleva_los_cuatro_filtros_y_la_inconsistencia_escapados(reglas):
    columnas = [Columna(c) for c in reglas.columnas]
    nodo = tmap("tMap_cuenta", [EntradaMap(ENTRADA, columnas)], salidas(reglas))
    xml = nodo.datos
    assert xml.count('activateExpressionFilter="true"') == 4
    assert "&amp;&amp;" in xml
    assert "&lt; 1" in xml
    assert "&quot;CODEX INVALIDO&quot;" in xml


def test_una_regla_que_no_es_rechazo_no_se_traduce(reglas):
    with pytest.raises(ValueError, match="no un rechazo"):
        fuera(replace(reglas.tipo_cta, permite=True))


def test_una_regla_sin_el_control_del_sas_no_se_traduce(reglas):
    with pytest.raises(ValueError, match="no trae el control"):
        fuera(replace(reglas.codex, control=None))


def test_un_rango_invertido_no_se_emite(reglas):
    with pytest.raises(ValueError, match="invertido"):
        fuera(replace(reglas.codex, desde=10, hasta=1))
