"""Fase 3.5 de `docs/automatizacion/03-plan-produccion.md`: fronteras entre programas.

Un conjunto permanente que un programa escribe y otro lee es una frontera: está persistido y
por eso no necesita tabla temporal.
"""

from __future__ import annotations

from sgm.compile import compile_project


def test_conjunto_permanente_escrito_y_leido_es_frontera() -> None:
    productor = "data lib.resultado; set work.base; run;\n"
    consumidor = "data work.copia; set lib.resultado; run;\n"
    compilados, _ = compile_project({"a.sas": productor, "b.sas": consumidor})
    assert compilados["a.sas"].plan.fronteras == ["LIB.resultado"] or compilados[
        "a.sas"
    ].plan.fronteras == ["lib.resultado"]
    assert compilados["b.sas"].plan.fronteras == []


def test_trabajo_no_es_frontera() -> None:
    compilados, _ = compile_project({"a.sas": "data work.x; set work.y; run;\n"})
    assert compilados["a.sas"].plan.fronteras == []
