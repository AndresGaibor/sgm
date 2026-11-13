"""B-13: la sentencia suma `x + expr;` (`lestmtsref`, p. 360).

La suma equivale a `RETAIN x 0; x = SUM(x, expr);`: `x` empieza en 0, se conserva de una iteración a la siguiente, y
un faltante en `expr` cuenta como 0, así que `x` nunca queda faltante. Como no tiene emisor en Talend todavía, el
traductor la deja como hueco (el Job no se escribe) y el intérprete la calcula.
"""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
FILAS = [{"id": "1", "x": "2"}, {"id": "2", "x": ""}, {"id": "3", "x": "5"}]


def _plan(cuerpo: str):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def test_la_suma_retiene_el_total_y_cuenta_el_faltante_como_cero():  # lestmtsref, p. 360
    salida = ejecutar_plan(_plan("  acum + x;\n"), {"t": FILAS})["r"]
    filas = [{k.lower(): v for k, v in f.items()} for f in salida]
    assert [float(f["acum"]) for f in filas] == [2.0, 2.0, 7.0]


def test_la_suma_no_se_puede_emitir_todavia_y_deja_hueco():  # lestmtsref, p. 360; decisión B-13
    plan = _plan("  acum + x;\n")
    sumas = [op for op in plan.graph.operators() if op.kind == "stateful_row"]
    assert sumas and sumas[0].status == "hueco"
    assert sumas[0].params.get("codigo") == "P-SUMA-SIN-EMISOR"
