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
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO 4;\n    a{i} = 0;\n  END;\n"
    assert any("do no traducido" in n for n in _notas(_plan(cuerpo)))


def test_limite_no_constante_queda_sin_desenrollar():
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO n;\n    a{i} = 0;\n  END;\n"
    assert any("do no traducido" in n for n in _notas(_plan(cuerpo)))


def test_output_dentro_del_bucle_no_se_desenrolla():
    cuerpo = "  ARRAY a{3} x1 x2 x3;\n  DO i = 1 TO 3;\n    a{i} = 0;\n    OUTPUT;\n  END;\n"
    assert any("do no traducido" in n for n in _notas(_plan(cuerpo)))
