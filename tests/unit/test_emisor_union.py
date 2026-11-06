"""`SET a b` y `UNION ALL` llegan al Job como `tUnite`, con una conexión de entrada por tabla."""

from __future__ import annotations

from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan
from sgm.talend_item.validador import validar_job

IMPORTAR = (
    "PROC IMPORT DATAFILE='.../{0}.csv' OUT=WORK.{0} DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
)


def _programa(tmp_path: Path, cuerpo: str, a: str, b: str):
    muestra = tmp_path / "muestra"
    muestra.mkdir()
    (muestra / "a.csv").write_text(a, encoding="utf-8")
    (muestra / "b.csv").write_text(b, encoding="utf-8")
    programa = tmp_path / "p.sas"
    programa.write_text(
        IMPORTAR.format("a")
        + IMPORTAR.format("b")
        + cuerpo
        + "PROC EXPORT DATA=WORK.t OUTFILE='.../t.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    return migrar(programa, tmp_path / "out", muestra=muestra)


def _reales(resultado) -> list:
    return [p for p in resultado.pendientes if p.codigo != "P-TIPO-DESCONOCIDO"]


def test_set_de_dos_tablas_con_las_mismas_columnas_es_un_tunite(tmp_path):
    resultado = _programa(
        tmp_path, "DATA WORK.t;\n  SET WORK.a WORK.b;\nRUN;\n", "id,v\n1,x\n", "id,v\n2,y\n"
    )

    job = resultado.jobs[0]
    unite = [n for n in job.nodos if n.componente == "tUnite"]
    entradas = [c.nombre for c in job.conexiones if unite and c.destino == unite[0].unico]

    assert _reales(resultado) == []
    assert len(unite) == 1
    assert len(entradas) == 2 and len(set(entradas)) == 2
    assert validar_job(job) == []


def test_columnas_distintas_dejan_la_union_pendiente(tmp_path):
    resultado = _programa(
        tmp_path, "DATA WORK.t;\n  SET WORK.a WORK.b;\nRUN;\n", "id,v\n1,x\n", "id,w\n2,y\n"
    )

    assert not any(n.componente == "tUnite" for j in resultado.jobs for n in j.nodos)
    assert "P-UNION-ESQUEMAS-DISTINTOS" in {p.codigo for p in resultado.pendientes}


def test_union_sin_all_queda_pendiente(tmp_path):
    consulta = (
        "PROC SQL;\n  CREATE TABLE WORK.t AS\n  SELECT id FROM WORK.a\n"
        "  UNION\n  SELECT id FROM WORK.b;\nQUIT;\n"
    )
    resultado = _programa(tmp_path, consulta, "id\n1\n", "id\n1\n")

    assert "P-UNION-SIN-ALL" in {p.codigo for p in resultado.pendientes}


def test_el_interprete_apila_por_nombre_y_rellena_con_faltante():
    texto = IMPORTAR.format("a") + IMPORTAR.format("b") + "DATA WORK.t;\n  SET WORK.a WORK.b;\nRUN;\n"
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan

    salida = ejecutar_plan(plan, {"a": [{"id": "1", "v": "x"}], "b": [{"id": "2", "w": "y"}]})

    assert salida["t"] == [
        {"id": "1", "v": "x", "w": None},
        {"id": "2", "v": None, "w": "y"},
    ]
