"""Hito 90 / R1-07: la regla de saldo negativo se lee del caso v05, no se inventa.

Los textos del caso y del programa de cliente se leen del repo. Las variantes se hacen por
sustitución de una sola cosa, para que cada prueba falle por una causa concreta.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sgm.proceso.reglas_saldo import (
    PENDIENTE_CERO,
    expandir_macros,
    negativos_a_cero,
    reglas_saldo,
)

RAIZ = Path(__file__).resolve().parents[2]
V05 = RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v05_codex_saldos" / "programa.sas"
CLIENTE = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
TEXTO_V05 = V05.read_text(encoding="utf-8", errors="replace")


def test_lee_la_regla_del_caso_v05():
    regla, _ = reglas_saldo(TEXTO_V05)
    assert regla.columna == "FIN_SALDO_CTA"
    assert regla.umbral == 0
    assert regla.motivo == "SALDO NEGATIVO"
    assert regla.productos == ("AHO", "CTE")
    assert regla.llave == "LLAVE_NOMBRE"
    assert regla.tablas == {"neg": "INCONS_SALDO_NEG", "valida": "SABANA_VALIDA"}


def test_las_proyecciones_son_las_del_sas():
    regla, _ = reglas_saldo(TEXTO_V05)
    # INCONS_SALDO_NEG_*: las ocho columnas del SELECT; la INCONSISTENCIA la añade el DATA.
    assert regla.proyeccion_neg == (
        "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
        "FIN_SALDO_CTA",
    )  # fmt: skip
    # SABANA_VALIDA_*: nueve columnas, con VAL_CRED_MES entre GMF y el saldo.
    assert regla.proyeccion_valida[-2:] == ("VAL_CRED_MES", "FIN_SALDO_CTA")
    assert len(regla.proyeccion_valida) == 9


def test_las_macros_se_expanden_por_sustitucion():
    expandido = expandir_macros(TEXTO_V05)
    assert "&sufijo" not in expandido
    # `SABANA_&sufijo..FIN_SALDO_CTA` tiene dos puntos: el primero delimita la macro.
    assert "SABANA_CTE.FIN_SALDO_CTA < 0" in expandido
    assert "SABANA_AHO.FIN_SALDO_CTA < 0" in expandido
    assert "%macro saldo_negativo" not in expandido


def test_el_programa_de_cliente_no_declara_el_rechazo():
    texto = CLIENTE.read_text(encoding="utf-8", errors="replace")
    with pytest.raises(ValueError, match="INCONS_SALDO_NEG_"):
        reglas_saldo(texto)


def test_el_cliente_pone_los_negativos_en_cero_y_se_publica():
    texto = CLIENTE.read_text(encoding="utf-8", errors="replace")
    assert negativos_a_cero(texto) is True
    assert negativos_a_cero(TEXTO_V05) is False
    assert "no los rechaza" in PENDIENTE_CERO


def test_el_where_debe_ser_una_sola_comparacion_menor_que_cero():
    mutado = TEXTO_V05.replace("FIN_SALDO_CTA < 0 ;", "FIN_SALDO_CTA <= 0 ;", 1)
    with pytest.raises(ValueError, match="alias.col < n"):
        reglas_saldo(mutado)


def test_sin_el_not_in_de_saldo_la_sabana_valida_no_se_acepta():
    mutado = re.sub(
        r"AND SABANA_&sufijo\.\.LLAVE_NOMBRE NOT IN\s*\(\s*SELECT NEG\.LLAVE_NOMBRE[^)]*\)\s*;",
        ";",
        TEXTO_V05,
    )
    assert mutado != TEXTO_V05
    with pytest.raises(ValueError, match="dos NOT IN"):
        reglas_saldo(mutado)


def test_sin_inconsistencia_no_hay_motivo_y_no_se_emite():
    mutado = TEXTO_V05.replace("INCONSISTENCIA='SALDO NEGATIVO';", "", 1)
    with pytest.raises(ValueError, match="INCONSISTENCIA"):
        reglas_saldo(mutado)


def test_un_motivo_distinto_se_lee_tal_cual_del_sas():
    mutado = TEXTO_V05.replace("'SALDO NEGATIVO'", "'SALDO NEG'")
    regla, _ = reglas_saldo(mutado)
    assert regla.motivo == "SALDO NEG"


def test_un_producto_sin_su_tabla_de_saldo_no_produce_regla():
    mutado = TEXTO_V05.replace("%saldo_negativo(AHO);", "")
    with pytest.raises(ValueError, match="no coinciden"):
        reglas_saldo(mutado)


def test_la_llave_pendiente_se_publica_como_salvedad():
    _, pendientes = reglas_saldo(TEXTO_V05)
    assert any("LLAVE_NOMBRE" in p and "R1-07" in p for p in pendientes)
