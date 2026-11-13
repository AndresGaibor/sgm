"""B-15: `SELECT/WHEN/OTHERWISE` se reduce a la cadena de `IF`, e `IF cond THEN DELETE` a un `filter`."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _plan(cuerpo: str):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _correr(cuerpo: str, filas: list[dict]) -> list[dict]:
    return ejecutar_plan(_plan(cuerpo), {"t": filas})["r"]


def _sin_traducir(plan) -> list[str]:
    return [t for op in plan.graph.operators() for t in op.params.get("untranslated", [])]


SELECT = (
    "  SELECT (x);\n"
    "    WHEN (1, 2) y = 'a';\n"
    "    WHEN (3) y = 'b';\n"
    "    OTHERWISE y = 'c';\n"
    "  END;\n"
)


def test_select_con_otherwise_coincide_con_la_cadena_de_if():
    salida = _correr(SELECT, [{"x": "1"}, {"x": "3"}, {"x": "2"}, {"x": "5"}, {"x": ""}])
    # El faltante no iguala a ningún WHEN: cae en OTHERWISE.
    assert [f["y"] for f in salida] == ["a", "b", "a", "c", "c"]


def test_select_sin_otherwise_queda_sin_traducir():
    cuerpo = "  SELECT (x);\n    WHEN (1) y = 'a';\n  END;\n"
    assert any("SELECT" in t for t in _sin_traducir(_plan(cuerpo)))


def test_delete_condicional_es_filtro_con_la_condicion_negada():
    cuerpo = "  z = k * 10;\n  IF k > 2 THEN DELETE;\n"
    salida = _correr(cuerpo, [{"k": "1"}, {"k": "3"}, {"k": "2"}])
    assert [(f["k"], f["z"]) for f in salida] == [("1", "10"), ("2", "20")]


def test_delete_tras_output_no_se_traduce():
    # Con OUTPUT antes no hay filtro: la nota lleva el código y no sale ningún `filter`.
    plan = _plan("  OUTPUT;\n  IF k > 2 THEN DELETE;\n")
    notas = [n for op in plan.graph.operators() for n in op.notes]
    assert any("P-DELETE-CON-OUTPUT" in n for n in notas)
    assert not any(op.kind == "filter" for op in plan.graph.operators())
