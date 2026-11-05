"""`PROC IMPORT` y `PROC EXPORT` con sus opciones de archivo en el IR.

El operador solo lleva lo que el texto del paso demuestra. `GETNAMES` ausente vale `YES` porque es
el valor por omisión documentado (`proc`, p. 1387); `DELIMITER` ausente queda en `None` y el emisor
lo trata como pendiente, porque el valor por omisión depende de la extensión (p. 1386).
"""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Operator


def _operador(texto: str, kind: str) -> Operator:
    analysis = analyze_program({"p.sas": texto})
    plan = compile_file(analysis, "p.sas", project_base()).plan
    return next(op for op in plan.graph.operators() if op.kind == kind)


def test_import_csv_con_getnames_y_delimitador():
    texto = """PROC IMPORT DATAFILE='a.csv' OUT=WORK.X DBMS=CSV REPLACE;
  GETNAMES=YES;
  DELIMITER=';';
RUN;
"""
    params = _operador(texto, "read_file").params

    assert params["dbms"] == "csv"
    assert params["getnames"] is True
    assert params["delimiter"] == ";"
    assert params["datafile"] == "'a.csv'"
    assert params["outputs"] == ["WORK.x"]


def test_import_xlsx_con_hoja():
    texto = """PROC IMPORT DATAFILE='b.xlsx' OUT=WORK.Y DBMS=XLSX REPLACE;
  SHEET="Hoja1";
RUN;
"""
    params = _operador(texto, "read_file").params

    assert params["dbms"] == "xlsx"
    assert params["sheet"] == "Hoja1"


def test_import_sin_getnames_usa_el_valor_por_omision():
    """`GETNAMES` ausente es `YES` en SAS (`proc`, p. 1387): no se inventa, se lee de la guía."""
    texto = """PROC IMPORT DATAFILE='a.csv' OUT=WORK.X DBMS=CSV REPLACE;
RUN;
"""
    params = _operador(texto, "read_file").params

    assert params["getnames"] is True
    assert params["delimiter"] is None


def test_import_con_getnames_no_y_guessingrows():
    texto = """PROC IMPORT DATAFILE='a.dlm' OUT=WORK.X DBMS=DLM REPLACE;
  DELIMITER='|';
  GETNAMES=NO;
  GUESSINGROWS=1000;
RUN;
"""
    params = _operador(texto, "read_file").params

    assert params["getnames"] is False
    assert params["delimiter"] == "|"
    assert params["guessingrows"] == 1000


def test_export_sin_delimitador_da_none():
    texto = """PROC EXPORT DATA=WORK.X OUTFILE='c.csv' DBMS=CSV REPLACE;
RUN;
"""
    params = _operador(texto, "write_file").params

    assert params["dbms"] == "csv"
    assert params["delimiter"] is None
    assert params["outfile"] == "'c.csv'"


def test_export_con_delimitador():
    texto = """PROC EXPORT DATA=WORK.X OUTFILE='c.txt' DBMS=DLM REPLACE;
  DELIMITER=';';
RUN;
"""
    params = _operador(texto, "write_file").params

    assert params["dbms"] == "dlm"
    assert params["delimiter"] == ";"
