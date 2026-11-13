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
    # B-21: el objeto hash es un hueco con su código; el `rc = h.find()` no sale como derive.
    ops = _operadores(PROGRAMA)
    assert not any(op.kind == "derive" and "find" in str(op.params) for op in ops)
    huecos = [op for op in ops if op.status == "hueco"]
    assert any(op.params.get("codigo") == "P-HASH-LOOKUP-SIN-SOPORTE" for op in huecos)
    assert all(op.status != "soportado" for op in ops if "find" in str(op.params).lower())
