"""Generador de joblets por grupo: regiones por macro repetida, grupos y contextos por miembro."""

from __future__ import annotations

from sgm.compile import compile_project
from sgm.facts.project import facts_for_project
from sgm.generador import joblets_por_grupo, marcador_de_regiones


def _bloque(nombre: str, tablas: list[str]) -> str:
    cuerpo = "".join(f"data work.{t}; set work.{nombre}_{t}; run;\n" for t in tablas)
    return f"%macro bloque;\n{cuerpo}%mend bloque;\n"


def test_regiones_son_definiciones_de_la_macro_mas_repetida() -> None:
    texto = "%macro otra; %mend otra;\n" + "".join(_bloque(f"a{i}", ["x"]) for i in range(3))
    inicios = marcador_de_regiones(texto.splitlines())
    assert len(inicios) == 3


def test_joblet_por_grupo_con_contexto_por_miembro() -> None:
    ventas = ["ventas_detalle", "ventas_resumen", "ventas_cierre"]
    texto = "".join(_bloque(f"a{i}", ventas) for i in range(3))
    compilados, _ = compile_project({"p.sas": texto})
    plan = compilados["p.sas"].plan
    hechos = facts_for_project({"p.sas": texto})["p.sas"]
    joblets = joblets_por_grupo(list(plan.graph.operators()), hechos, texto.splitlines())
    assert len(joblets) == 1
    assert joblets[0]["miembros"] == 3
    assert len(joblets[0]["contextos"]) == 3
