"""Subconsultas escalares, en FROM y EXISTS: hoy quedan pendientes, no salen como Job incorrecto (plan C, C-8 y C-9).

Mientras no haya traducción verificada, el migrador debe dejar el paso como pendiente con su motivo. Estas
pruebas fijan ese comportamiento para que un cambio futuro no lo convierta en un resultado silencioso.
"""

from __future__ import annotations

from sgm.cli_migrar import migrar

ESCALAR = """\
PROC IMPORT DATAFILE='ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.sobre_media AS
  SELECT id, monto FROM WORK.ventas WHERE monto > (SELECT AVG(monto) FROM WORK.ventas);
QUIT;
"""

FROM_SUBCONSULTA = """\
PROC IMPORT DATAFILE='ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.desde_subconsulta AS
  SELECT s.id FROM (SELECT id, monto FROM WORK.ventas WHERE monto > 15) s;
QUIT;
"""

EXISTS = """\
PROC IMPORT DATAFILE='ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='pagos.csv' OUT=WORK.PAGOS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.con_pago AS
  SELECT v.id, v.monto FROM WORK.ventas v
  WHERE EXISTS (SELECT 1 FROM WORK.pagos p WHERE p.id = v.id);
QUIT;
"""


def _codigos(tmp_path, texto: str) -> set[str]:
    (tmp_path / "ventas.csv").write_text("id,monto\n1,10\n2,30\n", encoding="utf-8")
    (tmp_path / "pagos.csv").write_text("id,cliente\n2,x\n", encoding="utf-8")
    programa = tmp_path / "programa.sas"
    programa.write_text(texto, encoding="utf-8")
    resultado = migrar(programa, tmp_path / "out", muestra=tmp_path)
    return {pendiente.codigo for pendiente in resultado.pendientes}


def test_subconsulta_escalar_en_where_queda_pendiente(tmp_path):
    assert _codigos(tmp_path, ESCALAR) & {"P-FILTRO-SIN-TRADUCIR", "P-OPERADOR-SIN-SOPORTE"}


def test_subconsulta_en_from_queda_pendiente(tmp_path):
    assert "P-OPERADOR-SIN-SOPORTE" in _codigos(tmp_path, FROM_SUBCONSULTA)


def test_exists_correlacionado_queda_pendiente(tmp_path):
    assert "P-FILTRO-SIN-TRADUCIR" in _codigos(tmp_path, EXISTS)
