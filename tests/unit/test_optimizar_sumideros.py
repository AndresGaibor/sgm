"""B-17: una asignación después del último `OUTPUT` no llega a ningún dataset; el diseño no la emite.

`lrcon`, p. 498: el PDV se escribe como observación en cada `OUTPUT`; lo que la sentencia `CONT = 1`
cambia después ya no entra en lo escrito, y sin salida el nodo deja una conexión colgada en Talend.
"""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.optimizar import optimizar

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _plan(cuerpo: str):
    texto = ENTRADA + "DATA WORK.S1 WORK.S2;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def test_asignacion_tras_output_sin_salida_se_quita_con_su_decision():
    plan = _plan("  OUTPUT WORK.S1;\n  CONT = 1;\n")
    nuevo, informe = optimizar(plan)
    assert not [op for op in nuevo.graph.operators() if op.kind == "derive"]
    assert [d.regla for d in informe.decisiones] == ["sumidero_muerto"]


def test_asignacion_antes_de_la_escritura_implicita_se_conserva():
    # Sin OUTPUT explícito, la asignación llega a la escritura implícita: no es un sumidero.
    plan = _plan("  CONT = 1;\n")
    nuevo, _ = optimizar(plan)
    assert [op for op in nuevo.graph.operators() if op.kind == "derive"]
