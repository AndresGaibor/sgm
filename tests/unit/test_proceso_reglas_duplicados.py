"""Hito 92 / R1-12: la regla de duplicados se lee del SAS, no se inventa.

Los textos vienen del caso `L8/01`, del caso `L6/l6_08` y del programa de cliente. Las variantes
cambian una sola cosa, para que cada prueba falle por una causa concreta.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas_duplicados import (
    MOTIVO,
    ReglaDuplicados,
    leer_reglas,
    regla_de_salida,
)

RAIZ = Path(__file__).resolve().parents[2]
L8_01 = RAIZ / "tests" / "corpus" / "L8" / "totales" / "01_duplicados_frecuencias" / "programa.sas"
L6_08 = RAIZ / "tests" / "corpus" / "L6" / "l6_08_nodupkey_llave" / "programa.sas"
CLIENTE = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
TEXTO_L8 = L8_01.read_text(encoding="utf-8", errors="replace")
TEXTO_L6 = L6_08.read_text(encoding="utf-8", errors="replace")
TEXTO_CLIENTE = CLIENTE.read_text(encoding="utf-8", errors="replace")


def test_lee_la_regla_del_caso_l8_01():
    regla = regla_de_salida(TEXTO_L8, "AHO_UNICOS")
    assert regla == ReglaDuplicados(
        entrada="AHO_ORDENADO",
        salida="AHO_UNICOS",
        llaves=("RELACION", "TIPO_CTA", "NRO_CTA", "TIPO_DOC", "NRO_DOC"),
        equals=True,
    )


def test_lee_la_regla_del_caso_l6_08():
    regla = regla_de_salida(TEXTO_L6, "CLIENTES_UNICOS")
    assert regla.entrada == "CLIENTES_DUP"
    assert regla.llaves == ("ID",)
    assert regla.equals is True
    assert regla.motivo == MOTIVO


def test_el_nodupkey_del_cliente_es_la_sabana_unica_de_neqii():
    regla = regla_de_salida(TEXTO_CLIENTE, "SABANA_DIR_UNICA_NEQUI")
    assert regla.entrada == "SABANA_COMPLETA_INFO_CLI_NEQUI"
    assert regla.llaves == ("NRO_DOC", "NRO_CTA")


def test_el_caso_l8_01_deja_pendiente_el_nodup_rec():
    _, pendientes = leer_reglas(TEXTO_L8)
    assert len(pendientes) == 1
    assert "AHO_SIN_DUPLICADOS_EXACTOS" in pendientes[0]
    assert "NODUPREC" in pendientes[0]


def test_sin_by_falla_con_value_error():
    texto = "PROC SORT DATA=WORK.A OUT=WORK.B NODUPKEY;\nRUN;"
    with pytest.raises(ValueError, match="sin BY"):
        leer_reglas(texto)


def test_sin_out_falla_con_value_error():
    texto = "PROC SORT DATA=WORK.A NODUPKEY;\nBY X;\nRUN;"
    with pytest.raises(ValueError, match="DATA= u OUT="):
        leer_reglas(texto)


def test_nodupkey_noequals_queda_pendiente_y_no_es_regla():
    texto = "PROC SORT DATA=WORK.A OUT=WORK.B NODUPKEY NOEQUALS;\nBY X;\nRUN;"
    reglas, pendientes = leer_reglas(texto)
    assert reglas == []
    assert "NOEQUALS" in pendientes[0]


def test_nodupkey_con_descending_queda_pendiente():
    texto = "PROC SORT DATA=WORK.A OUT=WORK.B NODUPKEY;\nBY DESCENDING X;\nRUN;"
    reglas, pendientes = leer_reglas(texto)
    assert reglas == []
    assert "DESCENDING" in pendientes[0]


def test_un_comentario_no_cuenta_como_sentencia():
    texto = "/* PROC SORT DATA=WORK.A OUT=WORK.B NODUPKEY; BY X; */\nRUN;"
    assert leer_reglas(texto) == ([], [])


def test_regla_de_salida_falla_si_no_hay_ninguna():
    with pytest.raises(ValueError, match="Se esperaba una regla"):
        regla_de_salida(TEXTO_L8, "NO_EXISTE")
