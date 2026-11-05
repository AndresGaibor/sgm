"""Hito 91 / R1-05: las expresiones del `tMap` de ubicación siguen la semántica de SAS.

Se comprueba la forma de cada expresión (literal a la izquierda, blancos finales fuera, nulos
seguros, longitud de SAS, mayúsculas neutras) y que el rechazo y el válido son complementarios.
La ejecución en Studio está en `tools/prueba_ubicacion.py`.
"""

from __future__ import annotations

from pathlib import Path

from sgm.proceso.reglas_ubicacion import reglas_ubicacion
from sgm.talend_item.filtros_ubicacion import (
    ENTRADA,
    LOOKUP_DANE,
    LOOKUP_PAIS,
    alternativas,
    faltante,
    longitud,
    motivo,
    rechazo,
    recortado,
    salidas,
)

RAIZ = Path(__file__).resolve().parents[2]
V03 = RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v03_pais_dane" / "programa.sas"
REGLA = reglas_ubicacion(V03.read_text(encoding="utf-8", errors="replace"))


def test_recortado_quita_solo_blancos_finales_y_tolera_nulo():
    expr = recortado("row1.PAIS")
    assert expr == '(row1.PAIS == null ? "" : row1.PAIS.replaceAll(" +$", ""))'


def test_faltante_es_texto_vacio_tras_recortar():
    assert faltante("CODIGO_UBICACION").endswith(".isEmpty()")
    assert "CODIGO_UBICACION" in faltante("CODIGO_UBICACION")


def test_longitud_de_sas_vale_uno_para_texto_en_blanco():
    expr = longitud("DIRECCION")
    assert "isEmpty() ? 1 :" in expr
    assert expr.endswith(".length())")


def test_el_literal_va_a_la_izquierda_en_equals():
    atomos = alternativas(REGLA)
    assert atomos["dane"].startswith('("900".equals(')
    assert '!"900".equals(' in atomos["extranjera"]


def test_el_pais_sin_pareja_usa_el_lookup_nulo():
    assert alternativas(REGLA)["pais"] == f"({LOOKUP_PAIS}.Codigo_Pais == null)"


def test_el_dane_sin_pareja_usa_el_lookup_nulo():
    assert f"{LOOKUP_DANE}.CODIGO_DANE == null" in alternativas(REGLA)["dane"]


def test_la_longitud_compara_con_el_umbral_del_caso():
    assert alternativas(REGLA)["longitud"].endswith(" < 8)")


def test_contains_usa_mayusculas_neutras_y_el_fragmento_en_mayusculas():
    fragmento = alternativas(REGLA)["fragmento"]
    assert "toUpperCase(java.util.Locale.ROOT)" in fragmento
    assert '.contains("SIN DIR")' in fragmento


def test_el_rechazo_es_la_union_de_las_cinco_alternativas():
    condicion = rechazo(REGLA)
    assert condicion.count("||") == 4
    assert condicion.startswith("(") and condicion.endswith(")")


def test_los_motivos_salen_del_caso_en_orden_de_case():
    expr = motivo(REGLA)
    posiciones = [
        expr.index(f'"{m}"')
        for m in (
            REGLA.motivo_pais,
            REGLA.motivo_dane,
            REGLA.motivo_extranjera,
            REGLA.motivo_direccion,
        )
    ]
    assert posiciones == sorted(posiciones)


def test_la_salida_de_rechazo_termina_en_inconsistencia_y_el_valido_la_niega():
    rechazo_map, valida_map = salidas(REGLA, ENTRADA)
    assert [c.nombre for c in rechazo_map.columnas][-1] == "INCONSISTENCIA"
    assert rechazo_map.filtro == rechazo(REGLA, ENTRADA)
    assert valida_map.filtro == "!" + rechazo(REGLA, ENTRADA)
    assert "INCONSISTENCIA" not in valida_map.expresiones


def test_las_salidas_leen_la_fila_de_entrada():
    rechazo_map, _ = salidas(REGLA, ENTRADA)
    assert rechazo_map.expresiones["PAIS"] == f"{ENTRADA}.PAIS"
    assert rechazo_map.expresiones["DIRECCION"] == f"{ENTRADA}.DIRECCION"


def test_la_clave_de_union_recorta_el_pais_y_el_codigo():
    from sgm.talend_item.filtros_ubicacion import clave_dane, clave_pais

    assert clave_pais() == recortado(f"{ENTRADA}.PAIS")
    assert clave_dane() == recortado(f"{ENTRADA}.CODIGO_UBICACION")
