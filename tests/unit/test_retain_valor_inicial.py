"""B-13: `RETAIN` con valor inicial y sin BY (`lestmtsref`, p. 331).

`RETAIN x 10;` inicializa `x` una sola vez, con el valor que se da; después `x` conserva su valor de una observación a
la siguiente. Sin BY, todo el conjunto es un solo grupo. El traductor no tiene emisor para el estado entre filas: el
paso no sale como Job (decisión 5) y el pendiente lleva el código `P-POR-GRUPO-SIN-EMISOR`. El intérprete lo calcula
para probarlo.
"""

from __future__ import annotations

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
FILAS = [{"id": "1", "x": "2"}, {"id": "2", "x": "3"}, {"id": "3", "x": "5"}]


def _plan(cuerpo: str):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _job_y_codigos(tmp_path, cuerpo: str):
    """Migra el programa completo: (jobs, códigos de pendiente)."""
    programa = tmp_path / "p.sas"
    programa.write_text(
        ENTRADA
        + "DATA WORK.r;\n  SET WORK.t;\n"
        + cuerpo
        + "RUN;\nPROC EXPORT DATA=WORK.r OUTFILE='r.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "t.csv").write_text("id,x\n1,2\n2,3\n", encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    return resultado.jobs, {p.codigo for p in resultado.pendientes}


def test_retain_con_valor_inicial_cuenta_desde_ese_valor():  # lestmtsref, p. 331
    salida = ejecutar_plan(_plan("  RETAIN s 10;\n  s = s + 1;\n"), {"t": FILAS})["r"]
    filas = [{k.lower(): v for k, v in f.items()} for f in salida]
    assert [float(f["s"]) for f in filas] == [11.0, 12.0, 13.0]


def test_retain_sin_by_no_sale_como_job(tmp_path):  # decisión 5 (B-13)
    jobs, codigos = _job_y_codigos(tmp_path, "  RETAIN s 10;\n  s = s + 1;\n")
    assert jobs == []
    assert "P-POR-GRUPO-SIN-EMISOR" in codigos
