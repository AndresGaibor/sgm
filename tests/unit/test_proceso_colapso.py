"""Tests del colapso por linaje: cadenas lineales, fontanería y bloques por etapa."""

from __future__ import annotations

from sgm.flow.model import build_flows
from sgm.flow.regiones import asignar_regiones, dividir_regiones
from sgm.proceso.colapso import SIN_ETAPA, colapsar, es_fontaneria, plantilla_por_etapa

# a -> b -> c es una cadena lineal (un bloque); c alimenta a d y a e (la tabla c persiste).
PROGRAMA = """\
data a; set entrada; run;
data b; set a; run;
data c; set b; run;
data d; set c; run;
data e; set c; run;
proc delete data=a b; run;
"""


def _modelo(texto: str = PROGRAMA):
    return build_flows({"p.sas": texto})["p.sas"]


def test_una_cadena_lineal_se_funde_y_lo_que_se_ramifica_no():
    modelo = _modelo()
    regiones = dividir_regiones(PROGRAMA, "%macro ambiente")
    colapso = colapsar(modelo, asignar_regiones(modelo, regiones))
    # a+b+c forman un bloque; d y e quedan aparte
    assert colapso.bloques == 3
    assert colapso.pasos_de_datos == 5


def test_los_pasos_de_borrado_son_fontaneria_y_no_cuentan():
    modelo = _modelo()
    borrado = next(p for p in modelo.steps if p.type_name == "PROC DELETE")
    assert es_fontaneria(borrado)
    assert colapsar(modelo, {}).pasos_totales == 6


def test_los_bloques_se_cuentan_por_etapa_del_primer_paso():
    modelo = _modelo()
    etapa = lambda paso: "carga" if paso.line <= 3 else "salida"  # noqa: E731
    colapso = colapsar(modelo, {}, etapa)
    assert colapso.bloques_por_region_etapa == {(0, "carga"): 1, (0, "salida"): 2}


def test_pasos_sin_etapa_caen_en_su_propia_clave():
    colapso = colapsar(_modelo(), {})
    assert set(e for (_r, e) in colapso.bloques_por_region_etapa) == {SIN_ETAPA}


def test_la_plantilla_cuenta_una_vez_la_familia_y_omite_las_etapas_eliminadas():
    modelo = _modelo()
    # Se reparten los bloques en 3 regiones falsas: 0 única, 1 y 2 familia (la 2 es mayor).
    ids = [p.id for p in modelo.steps if p.type_name != "PROC DELETE"]
    region = {ids[0]: 1, ids[1]: 1, ids[2]: 1, ids[3]: 2, ids[4]: 0}
    etapa = lambda paso: "persistir" if paso.line == 5 else "validar"  # noqa: E731
    colapso = colapsar(modelo, region, etapa)
    por_etapa = plantilla_por_etapa(colapso, [(1, 2)], [0], frozenset({"persistir"}))
    # región 0 (solo el paso e, etapa persistir) se omite; la familia (1,2) la representa la 1
    assert "persistir" not in por_etapa
    assert por_etapa == {"validar": 1}
