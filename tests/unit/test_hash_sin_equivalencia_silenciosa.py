"""B-21 (parte que ya cumple): un método de objeto hash no puede salir como paso soportado.

Un `h.find()` sin equivalente Talend queda `parcial` con la nota de expresión sin equivalente, y el
`declare hash` dentro de un `IF` sale como sentencia sin traducción. El lookup real (tMap con `rc`,
páginas 628-638 de `lrcon`) queda pendiente de B-21.
"""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program

PROGRAMA = """PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;
DATA WORK.r;
  SET WORK.t;
  DECLARE HASH h(dataset: 'work.b');
  rc = h.find();
  z = y;
RUN;
"""


def _operadores(texto: str):
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan.graph.operators()


def test_find_no_es_un_paso_soportado():
    ops = _operadores(PROGRAMA)
    derivados = [op for op in ops if op.kind == "derive"]
    assert derivados, "el paso con h.find() debe existir como derive"
    assert all(op.status != "soportado" for op in derivados)
    notas = [n for op in derivados for n in op.notes]
    assert any("h.find()" in n for n in notas)
