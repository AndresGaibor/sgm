"""Hito 86 / R1-04: el detector de filtros de fila lee el SAS, no lo supone."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas_fila import MODOS, flujos_producto, por_modo, reglas_fila

REPO = Path(__file__).resolve().parents[2]
REAL = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
V02 = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v02_vacios_ceros" / "programa.sas"


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8", errors="replace")


def test_v02_declara_exactamente_las_tres_reglas_con_alias_de_macro():
    reglas = reglas_fila(_texto(V02))
    assert [r.modo for r in reglas] == ["tit_cot", "fa", "valido"]
    assert all(r.columna == "NRO_DOC" for r in reglas)
    assert all("&sufijo" in r.destino for r in reglas)
    assert reglas[0].columna_relacion == "RELACION"
    assert reglas[0].valor_relacion == "9902"
    assert reglas[0].operador_relacion == "<>"
    assert reglas[1].operador_relacion == "="
    assert reglas[2].columna_relacion == ""
    assert reglas[0].linea < reglas[1].linea < reglas[2].linea


def test_el_programa_real_tiene_la_misma_terna_por_producto():
    reglas = reglas_fila(_texto(REAL))
    # Solo las seis tablas que `v02` reproduce. `FINAL_VALIDAR_NRO_DOC_CTE/AHO` también
    # termina en _CTE/_AHO, pero es una revalidación posterior, no la separación de flujos.
    prefijos = (
        "NRO_DOC_VACIO_0_TIT_COT_",
        "INCONS_NRO_DOC_VACIO_0_FA_",
        "NRO_DOC_NO_VACIO_NI_0_",
    )
    bloque = [r for r in reglas if r.destino.startswith(prefijos)]
    assert len(bloque) == 6
    assert {m: len(por_modo(bloque, m)) for m in MODOS} == {
        "tit_cot": 2, "fa": 2, "valido": 2
    }
    for producto in ("CTE", "AHO"):
        propios = [r for r in bloque if r.destino.endswith(producto)]
        assert {r.modo for r in propios} == set(MODOS)
        assert all(r.columna == "NRO_DOC" for r in propios)
        assert all(r.linea > 3000 for r in propios)


def test_el_mismo_where_aparece_en_otras_etapas_y_no_se_descarta_en_silencio():
    """Hay 10 reglas en el programa real: las 4 restantes son `valido` de NEQUI y del final."""
    reglas = reglas_fila(_texto(REAL))
    assert len(reglas) == 10
    assert len(por_modo(reglas, "valido")) == 6
    assert any(r.destino.startswith("FINAL_VALIDAR_NRO_DOC") for r in reglas)


@pytest.mark.parametrize(
    "where",
    [
        "WHERE ( ( A.NRO_DOC = 0 ) OR A.NRO_DOC IS MISSING ) AND ( A.RELACION <> 9902 )",
        "WHERE ((A.NRO_DOC=0) OR A.NRO_DOC IS MISSING) AND (A.RELACION <>9902)",
        "WHERE ( ( B.NRO_DOC = 0 ) OR B.NRO_DOC IS MISSING ) AND ( B.RELACION != 9902 )",
    ],
    ids=["normal", "sin_espacios", "alias_y_operador_distinto"],
)
def test_formas_del_where_de_tit_cot(where):
    sas = f"PROC SQL; CREATE TABLE WORK.X AS SELECT A.NRO_DOC FROM WORK.SABANA A {where}; QUIT;"
    reglas = reglas_fila(sas)
    assert len(reglas) == 1
    assert reglas[0].modo == "tit_cot"
    assert reglas[0].columna_relacion == "RELACION"
    assert reglas[0].valor_relacion == "9902"
    assert reglas[0].vacio_o_cero is True


def test_la_pareja_fa_y_la_regla_de_validos():
    fa = "PROC SQL; CREATE TABLE WORK.Y AS SELECT A.NRO_DOC FROM WORK.S A WHERE ( ( A.NRO_DOC = 0 ) OR A.NRO_DOC IS MISSING ) AND ( A.RELACION = 9902 ); QUIT;"
    valido = "PROC SQL; CREATE TABLE WORK.Z AS SELECT A.NRO_DOC FROM WORK.S A WHERE ( A.NRO_DOC IS NOT MISSING AND ( A.NRO_DOC <> 0 ) ); QUIT;"
    rfa, rval = reglas_fila(fa)[0], reglas_fila(valido)[0]
    assert (rfa.modo, rfa.operador_relacion) == ("fa", "=")
    assert rval.modo == "valido"
    assert rval.vacio_o_cero is False
    assert rval.columna_relacion == ""


def test_la_regla_de_campos_vacios_no_entra_porque_no_es_vacio_o_cero():
    sas = (
        "PROC SQL; CREATE TABLE WORK.INCONS_CAMPOS_VACIOS AS SELECT t1.NRO_DOC "
        "FROM WORK.S t1 WHERE t1.RELACION IS MISSING OR t1.NRO_DOC IS MISSING "
        "OR t1.GMF IS MISSING; QUIT;"
    )
    assert reglas_fila(sas) == []


def test_un_where_sin_la_forma_no_produce_reglas():
    sas = "PROC SQL; CREATE TABLE WORK.X AS SELECT A.NRO_DOC FROM WORK.S A WHERE A.RELACION = 9902; QUIT;"
    assert reglas_fila(sas) == []


def test_por_modo_rechaza_un_modo_desconocido():
    with pytest.raises(ValueError, match="desconocido"):
        por_modo([], "otro")


# Hito 87: además del WHERE se lee el SELECT, porque el Job emitido escribe esas columnas.
def test_la_proyeccion_sale_del_select_y_no_se_supone():
    v02 = [r.columnas for r in reglas_fila(_texto(V02))]
    separacion = ("NRO_DOC_VACIO_0_TIT_COT_", "INCONS_NRO_DOC_VACIO_0_FA_",
                  "NRO_DOC_NO_VACIO_NI_0_")
    real = [
        r.columnas for r in reglas_fila(_texto(REAL))
        if r.destino.startswith(separacion) and r.destino.endswith("_CTE")
    ]
    assert [len(c) for c in v02] == [6, 6, 7]
    assert v02[0][0] == "RELACION" and v02[2][-1] == "FIN_SALDO_CTA"
    assert [len(c) for c in real] == [19, 19, 19]
    assert real[0][0] == "RELACION" and real[0][-1] == "FIN_SALDO_CTA"


def test_un_select_con_expresiones_no_produce_una_proyeccion_inventada():
    sas = (
        "PROC SQL; CREATE TABLE WORK.X AS SELECT A.NRO_DOC, "
        "'NRO DOC VACIO O CERO' AS INCONSISTENCIA FROM WORK.S A "
        "WHERE ( ( A.NRO_DOC = 0 ) OR A.NRO_DOC IS MISSING ) "
        "AND ( A.RELACION <> 9902 ); QUIT;"
    )
    assert reglas_fila(sas)[0].columnas == ()


def test_flujos_producto_emite_una_terna_y_reporta_lo_que_queda_fuera():
    flujos, pendientes = flujos_producto(_texto(REAL))
    assert [f.modo for f in flujos] == list(MODOS)
    assert [f.tabla for f in flujos] == [
        "NRO_DOC_VACIO_0_TIT_COT", "INCONS_NRO_DOC_VACIO_0_FA", "NRO_DOC_NO_VACIO_NI_0"
    ]
    assert all(len(f.columnas) == 19 for f in flujos)
    assert any("FINAL_VALIDAR_NRO_DOC_CTE" in p for p in pendientes)
    assert any("Campos vacios" in p for p in pendientes)


def test_la_terna_de_v02_tiene_el_mismo_filtro_pero_otra_proyeccion():
    real, _ = flujos_producto(_texto(REAL))
    corpus, pendientes = flujos_producto(_texto(V02))
    assert [r.forma[:5] for r in real] == [r.forma[:5] for r in corpus]
    assert [len(r.columnas) for r in corpus] == [6, 6, 7]
    assert not any("revalidaciones" in p for p in pendientes)


def test_flujos_producto_no_mezcla_bloques_de_producto_distintos():
    texto = _texto(REAL).replace(
        "SABANA_NO_DUPLICADOS_CTE.RELACION <> 9902",
        "SABANA_NO_DUPLICADOS_CTE.RELACION <> 7777",
    )
    # El cambio del valor 9902 altera la forma del filtro de CTE, no solo el nombre de la tabla.
    with pytest.raises(ValueError, match="formas|distintos|proyección"):
        flujos_producto(texto)


def test_flujos_producto_falla_si_falta_un_flujo():
    with pytest.raises(ValueError, match="no declara el flujo"):
        flujos_producto("PROC SQL; QUIT;")
