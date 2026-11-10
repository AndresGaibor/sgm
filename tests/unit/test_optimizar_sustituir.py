"""Pruebas de `sustituir` y `es_columna`: qué nombres se consultan y qué texto queda.

El resolver de ayuda responde desde un diccionario (clave: nombre unido por puntos, en minúsculas)
y guarda cada lista de partes que recibió, para afirmar también lo que NO se le consultó.
"""

from __future__ import annotations

import pytest

from sgm.optimizar.sustituir import es_columna, sustituir

# Palabras reservadas que la prueba de reservadas recorre (las de la especificación).
RESERVADAS_PRUEBA = (
    "and or not in like between is null missing case when then else end eq ne gt lt ge le"
).split()


class Diccionario:
    """Resolver que sustituye desde un diccionario y anota cada consulta."""

    def __init__(self, columnas: dict[str, str]) -> None:
        self.columnas = columnas
        self.consultas: list[list[str]] = []

    def __call__(self, partes: list[str]) -> str | None:
        self.consultas.append(partes)
        return self.columnas.get(".".join(partes))


def test_sustituye_columna_simple():
    r = Diccionario({"monto": "(precio * cant)"})
    assert sustituir("monto", r) == "(precio * cant)"
    assert r.consultas == [["monto"]]


def test_nombre_calificado_se_consulta_con_sus_partes():
    r = Diccionario({"ventas.monto": "precio"})
    assert sustituir("ventas.monto * 2", r) == "precio * 2"
    assert r.consultas == [["ventas", "monto"]]


def test_nombre_de_tres_partes_se_consulta_completo():
    r = Diccionario({"work.ventas.monto": "precio"})
    assert sustituir("work.ventas.monto", r) == "precio"
    assert r.consultas == [["work", "ventas", "monto"]]


def test_comodin_t_asterisco_llega_como_partes():
    r = Diccionario({})
    assert sustituir("t.*", r) == "t.*"
    assert r.consultas == [["t", "*"]]


def test_mayusculas_llegan_en_minusculas():
    r = Diccionario({"monto": "precio", "ventas.monto": "ingreso"})
    assert sustituir("MONTO + Ventas.Monto", r) == "precio + ingreso"
    assert r.consultas == [["monto"], ["ventas", "monto"]]


def test_literal_de_texto_con_el_nombre_no_se_toca():
    r = Diccionario({"monto": "ventas"})
    entrada = "monto = 'monto' and monto = \"monto\""
    assert sustituir(entrada, r) == "ventas = 'monto' and ventas = \"monto\""
    assert r.consultas == [["monto"], ["monto"]]


def test_comilla_doblada_dentro_del_literal_no_se_toca():
    r = Diccionario({"monto": "ventas"})
    assert sustituir("'it''s monto' || monto", r) == "'it''s monto' || ventas"
    assert r.consultas == [["monto"]]


def test_funcion_no_se_toca_pero_sus_argumentos_si():
    r = Diccionario({"upcase": "ERROR", "monto": "precio"})
    assert sustituir("upcase(monto)", r) == "upcase(precio)"
    assert r.consultas == [["monto"]]


def test_funcion_con_espacios_antes_del_parentesis_no_se_toca():
    r = Diccionario({"upcase": "ERROR", "monto": "precio"})
    assert sustituir("upcase   (monto)", r) == "upcase   (precio)"
    assert r.consultas == [["monto"]]


def test_palabras_reservadas_no_se_consultan():
    r = Diccionario({w: "ERROR" for w in RESERVADAS_PRUEBA})
    entrada = " ".join(RESERVADAS_PRUEBA)
    assert sustituir(entrada, r) == entrada
    assert sustituir(entrada.upper(), r) == entrada.upper()
    assert r.consultas == []


def test_macrovariable_no_se_toca():
    r = Diccionario({"anio": "ERROR", "monto": "ventas"})
    assert sustituir("monto + &anio", r) == "ventas + &anio"
    assert r.consultas == [["monto"]]


def test_sufijo_de_literal_de_fecha_no_se_consulta():
    r = Diccionario({"fecha": "fecha_real", "d": "ERROR"})
    assert sustituir("fecha >= '01JAN2020'd", r) == "fecha_real >= '01JAN2020'd"
    assert r.consultas == [["fecha"]]


def test_numeros_no_se_consultan():
    r = Diccionario({"e5": "ERROR", "monto": "ventas"})
    assert sustituir("monto * 2.5 + 1e5 - 2", r) == "ventas * 2.5 + 1e5 - 2"
    assert r.consultas == [["monto"]]


def test_resolver_none_deja_el_texto_igual_con_espacios():
    r = Diccionario({})
    entrada = "  monto   *  2 "
    assert sustituir(entrada, r) == entrada
    assert r.consultas == [["monto"]]


@pytest.mark.parametrize("texto", ["monto", "ventas.monto"])
def test_es_columna_acepta_nombres(texto: str):
    assert es_columna(texto)


@pytest.mark.parametrize("texto", ["monto * 2", "upcase(x)", "'a'", ""])
def test_es_columna_rechaza_otras_expresiones(texto: str):
    assert not es_columna(texto)
