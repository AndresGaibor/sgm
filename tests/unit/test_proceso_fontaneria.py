"""Tests de la sección 6: equivalencias de fontanería con su cuenta."""

from __future__ import annotations

from sgm.frontend.program import analyze_program
from sgm.proceso.fontaneria import contar_fontaneria, seccion_equivalencias

PROGRAMA = """\
%put paso uno;
%put paso dos;
data a; x = 1; run;
title 'reporte';
"""


def _equivalencias():
    items = analyze_program({"p.sas": PROGRAMA}, {}).items
    return contar_fontaneria(items)


def test_cuenta_cada_categoria_y_ordena_de_mayor_a_menor():
    eqs = _equivalencias()
    cuentas = {e.categoria: e.cantidad for e in eqs}
    assert cuentas["mensajes"] == 2
    assert cuentas["presentacion"] == 1
    assert [e.cantidad for e in eqs] == sorted((e.cantidad for e in eqs), reverse=True)


def test_un_paso_de_datos_no_es_fontaneria():
    assert all(e.categoria != "data" for e in _equivalencias())
    assert sum(e.cantidad for e in _equivalencias()) == 3


def test_la_seccion_pone_la_cuenta_en_la_clave_y_el_texto_de_la_regla_en_el_valor():
    seccion = seccion_equivalencias(_equivalencias())
    clave = next(k for k in seccion if k.endswith("(2)"))
    assert "%put" in clave
    assert "tLogRow" in seccion[clave]["equivalente_talend"]
