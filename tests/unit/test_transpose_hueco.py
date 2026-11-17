"""B-8: `PROC TRANSPOSE` sale como pivote en estado `hueco`, con su página, y el pendiente es `P-OPERADOR-PIVOTAR`."""

from __future__ import annotations

from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program

PROGRAMA = """PROC SORT DATA=WORK.a; BY id; RUN;
PROC TRANSPOSE DATA=WORK.a OUT=WORK.b; BY id; VAR x; RUN;
"""


def test_transpose_es_un_pivote_hueco_con_su_pagina(tmp_path: Path) -> None:
    plan = compile_file(
        analyze_program({"t.sas": PROGRAMA}), "t.sas", project_base()
    ).plan
    pivotes = [op for op in plan.graph.operators() if op.kind == "pivot"]
    assert len(pivotes) == 1
    assert pivotes[0].status == "hueco"
    assert "p. 2745" in pivotes[0].notes[0]


def test_el_pendiente_de_transpose_tiene_su_codigo(tmp_path: Path) -> None:
    programa = tmp_path / "t.sas"
    programa.write_text(PROGRAMA, encoding="utf-8")
    resultado = migrar(programa, tmp_path / "out")
    assert "P-OPERADOR-PIVOTAR" in {p.codigo for p in resultado.pendientes}
