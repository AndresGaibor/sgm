"""B-13: la sentencia suma `x + expr;` (`lestmtsref`, p. 360).

La suma equivale a `RETAIN x 0; x = SUM(x, expr);`: `x` empieza en 0, se conserva de una iteración a la siguiente, y
un faltante en `expr` cuenta como 0, así que `x` nunca queda faltante. Sin emisor en Talend todavía, el paso no sale
como Job (decisión 5) y el intérprete la calcula para probarla.
"""

from __future__ import annotations

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
FILAS = [{"id": "1", "x": "2"}, {"id": "2", "x": ""}, {"id": "3", "x": "5"}]


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
    (muestra / "t.csv").write_text("id,x\n1,2\n2,\n3,5\n", encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    return resultado.jobs, {p.codigo for p in resultado.pendientes}


def test_la_suma_retiene_el_total_y_cuenta_el_faltante_como_cero():  # lestmtsref, p. 360
    salida = ejecutar_plan(_plan("  acum + x;\n"), {"t": FILAS})["r"]
    filas = [{k.lower(): v for k, v in f.items()} for f in salida]
    assert [float(f["acum"]) for f in filas] == [2.0, 2.0, 7.0]


def test_la_suma_no_sale_como_job_hasta_tener_emisor(tmp_path):  # decisión 5 (B-13)
    jobs, codigos = _job_y_codigos(tmp_path, "  acum + x;\n")
    assert jobs == []
    assert "P-POR-GRUPO-SIN-EMISOR" in codigos
