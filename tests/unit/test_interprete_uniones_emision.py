"""El emisor no reproduce la condición residual de un JOIN (`m.v < n.v`): queda como pendiente (plan C-5)."""

from __future__ import annotations

from sgm.cli_migrar import migrar

PROGRAMA = """\
PROC IMPORT DATAFILE='p.csv' OUT=WORK.P DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.pares AS
  SELECT m.a, m.v AS v1, n.v AS v2 FROM WORK.P m INNER JOIN WORK.P n
  ON m.a = n.a AND m.v < n.v;
QUIT;
"""


def test_el_auto_join_con_condicion_residual_queda_pendiente_en_el_job(tmp_path):
    (tmp_path / "p.csv").write_text("a,b,v\nA,,1\nA,x,2\nB,y,3\n", encoding="utf-8")
    programa = tmp_path / "programa.sas"
    programa.write_text(PROGRAMA, encoding="utf-8")

    resultado = migrar(programa, tmp_path / "out", muestra=tmp_path)

    codigos = {pendiente.codigo for pendiente in resultado.pendientes}
    assert "P-UNION-TIPO-SIN-SOPORTE" in codigos
