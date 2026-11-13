"""B-16: `ARRAY` y `DO` con límites constantes se desenrollan; lo demás queda sin traducir."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _plan(cuerpo: str):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _notas(plan) -> list[str]:
    return [n for op in plan.graph.operators() for n in op.notes]


def test_do_constante_sobre_arreglo_se_desenrolla_y_deja_i_en_el_limite_mas_uno():
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO 3;\n    a{i} = a{i} * 2;\n  END;\n"
    salida = ejecutar_plan(_plan(cuerpo), {"t": [{"x1": "1", "x2": "2", "x3": "3"}]})["r"]
    fila = salida[0]
    assert [float(fila[c]) for c in ("x1", "x2", "x3")] == [2.0, 4.0, 6.0]
    assert float(fila["i"]) == 4.0


def test_indice_fuera_de_rango_no_se_inventa():
    # Hueco: el paso no se emite, y no sale ninguna asignación a las columnas del arreglo.
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO 4;\n    a{i} = 0;\n  END;\n"
    plan = _plan(cuerpo)
    assert any(op.status == "hueco" for op in plan.graph.operators())
    assert not any(op.kind == "derive" for op in plan.graph.operators())


def test_indice_fuera_de_rango_lleva_el_codigo_con_su_pagina():
    # lrcon, p. 192: el índice fuera de rango es error de ejecución; el paso se detiene.
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO 4;\n    a{i} = 0;\n  END;\n"
    notas = _notas(_plan(cuerpo))
    assert any("P-ARRAY-FUERA-DE-RANGO" in n and "a{4}" in n and "lrcon, p. 192" in n for n in notas)


def test_indice_dentro_de_rango_no_lleva_codigo_de_fuera_de_rango():
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO 3;\n    a{i} = 0;\n  END;\n"
    assert not any("P-ARRAY-FUERA-DE-RANGO" in n for n in _notas(_plan(cuerpo)))


def test_limite_no_constante_queda_sin_desenrollar():
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO n;\n    a{i} = 0;\n  END;\n"
    assert any("do no traducido" in n for n in _notas(_plan(cuerpo)))


def test_do_while_lleva_el_codigo_p_do_while_until():
    # lrcon, p. 675: DO WHILE/UNTIL con referencias a arreglos; aquí no se desenrolla (sin Studio).
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO WHILE (x1 < 5);\n    a{1} = a{1} + 1;\n  END;\n"
    plan = _plan(cuerpo)
    assert any("P-DO-WHILE-UNTIL" in n and "lrcon, p. 675" in n for n in _notas(plan))
    # Hueco: el cuerpo del bucle no genera asignaciones aparte.
    assert any(op.status == "hueco" for op in plan.graph.operators())
    assert not any(op.kind == "derive" for op in plan.graph.operators())


def test_output_dentro_del_bucle_no_se_desenrolla():
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO 3;\n    a{i} = 0;\n    OUTPUT;\n  END;\n"
    assert any("do no traducido" in n for n in _notas(_plan(cuerpo)))
