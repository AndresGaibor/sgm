"""Fase 4.1 de `docs/automatizacion/03-plan-produccion.md`: la guía muestra los joblets."""

from __future__ import annotations

from sgm.compile import compile_project
from sgm.emit.guide_md import render_guide

PROGRAMA = """/* Etiqueta: Bloque A */
data work.a1; set work.s1; x = 1; y = x + 2; z = y * 3; run;
data work.a2; set work.s2; x = 1; y = x + 2; z = y * 3; run;
data work.a3; set work.s3; x = 1; y = x + 2; z = y * 3; run;
/* Etiqueta: Bloque B */
data work.b1; set work.t1; x = 1; y = x + 2; z = y * 3; run;
data work.b2; set work.t2; x = 1; y = x + 2; z = y * 3; run;
"""


def test_guia_muestra_joblet_con_parametros_y_apariciones() -> None:
    compilados, _ = compile_project({"x.sas": PROGRAMA})
    guia = render_guide(compilados["x.sas"].plan)
    assert "## Joblets" in guia
    assert "### jl_" in guia
    assert "Apariciones:" in guia
    assert "Entradas (de fuera del bloque):" in guia
    assert "Salidas (para el resto del programa):" in guia


def test_sin_joblets_no_hay_seccion() -> None:
    compilados, _ = compile_project({"x.sas": "data work.a; set work.b; run;\n"})
    assert "## Joblets" not in render_guide(compilados["x.sas"].plan)
