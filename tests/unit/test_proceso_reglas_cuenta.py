"""Hito 88 / R1-06: las reglas de cuenta y GMF salen del SAS, no del traductor."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas import reglas as reglas_rango
from sgm.proceso.reglas_cuenta import _partes, proyecciones, reglas_cuenta

REPO = Path(__file__).resolve().parents[2]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v04_tipo_cta_gmf"
REAL = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"


@pytest.fixture(scope="module")
def texto() -> str:
    return (CASO / "programa.sas").read_text(encoding="utf-8")


def test_la_lista_de_tipos_de_cuenta_viene_del_not_in(texto):
    r = reglas_cuenta(texto)

    assert r.columna_lista == "TIPO_CTA"
    assert r.valores == ("1", "2", "3", "4", "5")


def test_el_rango_y_el_faltante_vienen_del_where_del_gmf(texto):
    r = reglas_cuenta(texto)

    assert (r.columna_rango, r.desde, r.hasta) == ("GMF", 1, 10)
    assert r.con_faltante is True


def test_los_tres_motivos_salen_del_case_y_del_union(texto):
    r = reglas_cuenta(texto)

    assert r.motivos == {
        "lista": "TIPO CTA INVALIDO",
        "faltante": "GMF NO NUMERICO",
        "rango": "GMF FUERA DE RANGO",
    }


def test_el_informat_y_el_alias_de_la_columna_de_texto_salen_del_data_step(texto):
    r = reglas_cuenta(texto)

    assert r.informat == (3, 0)
    assert r.columna_texto == "GMF_TXT"
    assert r.alias["GMF_TXT"] == "VAR11"
    assert r.alias["FIN_SALDO_CTA"] == "VAR23"
    assert r.alias["TIPO_CTA"] == "VAR6"


def test_las_cuatro_proyecciones_son_las_de_los_create_table(texto):
    r = reglas_cuenta(texto)

    assert r.proyecciones == {
        "tipo_cta": ("RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF"),
        "gmf": (
            "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
            "MOTIVO",
        ),
        "valido": (
            "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
            "FIN_SALDO_CTA",
        ),
        "cuenta": ("RELACION", "TIPO_CTA", "LLAVE_NOMBRE", "GMF", "INCONSISTENCIA"),
    }


def test_las_proyecciones_coinciden_con_las_cabeceras_de_los_esperados(texto):
    import csv

    from sgm.proceso.reglas_cuenta import TABLAS

    r = reglas_cuenta(texto)
    for modo, tabla in TABLAS.items():
        nombre = "INCONS_CUENTA_CTE.csv" if modo == "cuenta" else tabla.replace("&SUFIJO", "CTE") + ".csv"
        with (CASO / "esperado" / nombre).open(encoding="utf-8", newline="") as archivo:
            cabecera = tuple(next(csv.reader(archivo, delimiter=",")))
        assert r.proyecciones[modo] == cabecera


def test_el_select_del_case_y_del_count_no_rompe_el_partidor():
    partes = _partes(
        "a.COL, CASE WHEN a.GMF IS MISSING THEN 'GMF NO NUMERICO' ELSE 'OTRO' END AS MOTIVO, "
        "COUNT(*) AS NRO, 'TIPO CTA INVALIDO' AS INCONSISTENCIA"
    )

    assert len(partes) == 4
    assert "END AS MOTIVO" in partes[1]


def test_las_formas_del_programa_real_coinciden_en_rango_pero_no_en_motivo(texto):
    """No se unifican las dos escrituras: el real llama CODEX INVALIDO al rango de GMF."""
    reales = {
        (r.columna.upper(), r.desde, r.hasta, r.permite)
        for r in reglas_rango(REAL.read_text(encoding="latin-1"))
    }
    corpus = reglas_cuenta(texto)

    assert ("TIPO_CTA", 1, 5, False) in reales
    assert ("GMF", 1, 10, False) in reales
    assert (corpus.desde, corpus.hasta) == (1, 10)
    assert corpus.motivos["rango"] != "CODEX INVALIDO"


@pytest.mark.parametrize(
    "quitado",
    ["NOT IN", "IS MISSING", "WHEN", "input(left("],
)
def test_un_programa_sin_alguna_de_las_declaraciones_no_produce_reglas_a_medias(texto, quitado):
    recortado = texto.replace(quitado, "XX", 1) if quitado != "input(left(" else texto.replace(
        "input(left(GMF_TXT)", "sin_conversion(GMF_TXT)", 1
    )
    with pytest.raises(ValueError):
        reglas_cuenta(recortado)


def test_dos_proyecciones_distintas_para_la_misma_tabla_se_rechazan():
    sas = (
        "proc sql; create table work.igual as select a.UNO from work.x a; quit;"
        "proc sql; create table work.igual as select a.DOS from work.x a; quit;"
    )
    with pytest.raises(ValueError, match="dos proyecciones distintas"):
        proyecciones(sas)
