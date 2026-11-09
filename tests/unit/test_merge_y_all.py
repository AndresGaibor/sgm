"""`MERGE ... BY` (interprete y emisor) y `BY _ALL_` en `PROC SORT`."""

from __future__ import annotations

from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

IMPORTAR = (
    "PROC IMPORT DATAFILE='.../{0}.csv' OUT=WORK.{0} DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
)


def _plan(cuerpo: str):
    texto = IMPORTAR.format("a") + IMPORTAR.format("b") + cuerpo
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


A = [
    {"id": "1", "x": "a1"},
    {"id": "2", "x": "a2"},
    {"id": "2", "x": "a2b"},
    {"id": "4", "x": "a4"},
]
B = [{"id": "2", "y": "b2"}, {"id": "3", "y": "b3"}, {"id": "4", "y": "b4"}]


def test_merge_completo_junta_fila_con_fila_y_no_hace_producto():
    plan = _plan("DATA WORK.t;\n  MERGE WORK.a WORK.b;\n  BY id;\nRUN;\n")

    filas = ejecutar_plan(plan, {"a": A, "b": B})["t"]

    # La llave 2 tiene dos filas en `a` y una en `b`: la de `b` se repite (SQL daría lo mismo),
    # pero la 3 solo está en `b` y la 1 solo en `a`, que un cruce interno perdería.
    assert [(f["id"], f["x"], f["y"]) for f in filas] == [
        ("1", "a1", None),
        ("2", "a2", "b2"),
        ("2", "a2b", "b2"),
        ("3", None, "b3"),
        ("4", "a4", "b4"),
    ]


def test_merge_con_if_de_la_bandera_se_queda_con_las_filas_de_la_primera():
    plan = _plan("DATA WORK.t;\n  MERGE WORK.a(IN=ea) WORK.b(IN=eb);\n  BY id;\n  IF ea;\nRUN;\n")

    filas = ejecutar_plan(plan, {"a": A, "b": B})["t"]

    assert [(f["id"], f["ea"], f["eb"]) for f in filas] == [
        ("1", 1, 0),
        ("2", 1, 1),
        ("2", 1, 1),
        ("4", 1, 1),
    ]


def test_el_merge_con_if_de_la_primera_queda_pendiente_y_no_sale_como_tmap(tmp_path: Path):
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "a.csv").write_text("id,x\n1,a\n", encoding="utf-8")
    (muestra / "b.csv").write_text("id,y\n1,b\n", encoding="utf-8")
    programa = tmp_path / "p.sas"
    programa.write_text(
        IMPORTAR.format("a")
        + IMPORTAR.format("b")
        + "DATA WORK.t;\n  MERGE WORK.a(IN=ea) WORK.b(IN=eb);\n  BY id;\n  IF ea;\nRUN;\n"
        + "PROC EXPORT DATA=WORK.t OUTFILE='.../t.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )

    resultado = migrar(programa, tmp_path / "out", muestra=muestra)

    # Un MERGE no se emite como tMap: el tMap cruza por llave y no hace el emparejamiento fila con
    # fila de SAS cuando la llave se repite. Queda como pendiente con motivo.
    codigos = {p.codigo for p in resultado.pendientes}
    assert "P-UNION-TIPO-SIN-SOPORTE" in codigos
    job = resultado.jobs[0]
    assert not any(n.componente == "tMap" for n in job.nodos)


def test_el_merge_completo_queda_pendiente_porque_un_tmap_no_hace_full_outer(tmp_path: Path):
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "a.csv").write_text("id,x\n1,a\n", encoding="utf-8")
    (muestra / "b.csv").write_text("id,y\n1,b\n", encoding="utf-8")
    programa = tmp_path / "p.sas"
    programa.write_text(
        IMPORTAR.format("a")
        + IMPORTAR.format("b")
        + "DATA WORK.t;\n  MERGE WORK.a WORK.b;\n  BY id;\nRUN;\n"
        + "PROC EXPORT DATA=WORK.t OUTFILE='.../t.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )

    resultado = migrar(programa, tmp_path / "out", muestra=muestra)

    assert "P-UNION-TIPO-SIN-SOPORTE" in {p.codigo for p in resultado.pendientes}


def test_by_all_ordena_y_quita_repetidos_por_todas_las_columnas():
    plan = _plan("PROC SORT DATA=WORK.a OUT=WORK.t NODUP;\n  BY _ALL_;\nRUN;\n")
    filas = [{"id": "2", "x": "p"}, {"id": "1", "x": "q"}, {"id": "2", "x": "p"}]

    salida = ejecutar_plan(plan, {"a": filas, "b": []})["t"]

    assert salida == [{"id": "1", "x": "q"}, {"id": "2", "x": "p"}]
