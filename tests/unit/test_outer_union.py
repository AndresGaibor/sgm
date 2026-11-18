"""OUTER UNION CORR concatena por nombre (sqlproc.pdf, p. 135)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.frontend.sql_normalize import normalize
from sgm.ir.sql_render import render
from sgm.ir.sql_tree import build
from sgm.migrar.interprete import NoSoportadoEnInterprete, ejecutar_plan


def _plan(query):
    text = f"PROC SQL; CREATE TABLE WORK.r AS {query}; QUIT;"
    return compile_file(analyze_program({"p.sas": text}), "p.sas", project_base()).plan


def test_corr_aligns_names_and_preserves_first_appearance_and_all_rows():
    plan = _plan("SELECT id,x FROM WORK.a OUTER UNION CORR SELECT y,id FROM WORK.b")
    rows = ejecutar_plan(plan, {
        "a": [{"id": "1", "x": "10"}, {"id": "1", "x": "10"}],
        "b": [{"id": "3", "y": "30"}],
    })["r"]
    assert list(rows[0]) == ["id", "x", "y"]
    assert rows == [
        {"id": "1", "x": "10", "y": None},
        {"id": "1", "x": "10", "y": None},
        {"id": "3", "x": None, "y": "30"},
    ]


def test_corr_keeps_columns_from_an_empty_explicit_branch():
    plan = _plan("SELECT id,x FROM WORK.a OUTER UNION CORR SELECT id,y FROM WORK.b")
    assert ejecutar_plan(plan, {"a": [], "b": [{"id": "3", "y": "30"}]})["r"] == [
        {"id": "3", "x": None, "y": "30"},
    ]


def test_empty_star_without_demonstrated_schema_is_explicit():
    plan = _plan("SELECT * FROM WORK.a OUTER UNION CORR SELECT id,y FROM WORK.b")
    with pytest.raises(NoSoportadoEnInterprete, match="sin esquema demostrado"):
        ejecutar_plan(plan, {"a": [], "b": [{"id": "3", "y": "30"}]})


def test_corr_chains_stars_and_named_expressions_case_insensitively():
    plan = _plan(
        "SELECT * FROM WORK.a OUTER UNION CORRESPONDING SELECT ID,y FROM WORK.b "
        "OUTER UNION CORR SELECT id, z AS extra FROM WORK.c"
    )
    rows = ejecutar_plan(plan, {
        "a": [{"id": "1", "x": "10"}], "b": [{"ID": "2", "y": "20"}],
        "c": [{"id": "3", "z": "30"}],
    })["r"]
    assert list(rows[0]) == ["id", "x", "y", "extra"]
    assert rows[-1] == {"id": "3", "x": None, "y": None, "extra": "30"}
    assert len(rows) == 3


def test_non_corr_repeated_names_has_specific_pending():
    plan = _plan("SELECT id,x FROM WORK.a OUTER UNION SELECT id,y FROM WORK.b")
    [op] = [op for op in plan.graph.operators() if op.kind == "unsupported"]
    assert op.params["pending_code"] == "P-OUTER-UNION-COLUMNAS-REPETIDAS"
    assert not any(op.kind == "union" for op in plan.graph.operators())


@pytest.mark.parametrize("query", [
    "SELECT x FROM a OUTER UNION SELECT y FROM b",
    "SELECT id,x+x FROM a OUTER UNION CORR SELECT id FROM b",
    "SELECT id,id FROM a OUTER UNION CORR SELECT id FROM b",
    "SELECT id FROM a OUTER UNION CORR SELECT id FROM b UNION SELECT id FROM c",
    "SELECT id FROM a OUTER UNION CORR SELECT id FROM b ORDER BY id",
    "SELECT DISTINCT id FROM a OUTER UNION CORR SELECT id FROM b",
])
def test_unproven_forms_stay_pending(query):
    plan = _plan(query)
    assert any(op.kind == "unsupported" for op in plan.graph.operators())
    assert not any(op.kind == "union" for op in plan.graph.operators())


def test_outer_union_words_inside_a_literal_do_not_change_the_query():
    plan = _plan("SELECT 'outer union corr' AS label FROM a")
    assert ejecutar_plan(plan, {"a": [{"id": "1"}]})["r"] == [{"label": "outer union corr"}]


def test_corr_cannot_be_rendered_as_positional_union_all():
    sql = normalize("SELECT id,x FROM a OUTER UNION CORR SELECT id,y FROM b")
    tree = build(sql.text)
    with pytest.raises(ValueError, match="OUTER UNION CORR"):
        render(tree, sql)


def test_corr_corpus_emits_valid_static_job_with_aligned_union(tmp_path):
    from sgm.cli_migrar import migrar
    from sgm.talend_item.validador import validar_job

    case = Path(__file__).resolve().parents[1] / "corpus/L3/l3_21_outer_union_corr"
    result = migrar(case / "programa.sas", tmp_path / "out", muestra=case / "entradas")
    assert result.pendientes == []
    assert result.jobs
    assert all(validar_job(job) == [] for job in result.jobs)
    unions = [node for job in result.jobs for node in job.nodos if node.componente == "tUnite"]
    assert len(unions) == 1
    assert [c.nombre for c in unions[0].metadatas[0].columnas] == ["id", "x", "y"]


def test_non_corr_pending_reaches_migration_report(tmp_path):
    from sgm.cli_migrar import migrar

    source = tmp_path / "p.sas"
    source.write_text(
        "PROC SQL; CREATE TABLE r AS SELECT id FROM a OUTER UNION SELECT id FROM b; QUIT;",
        encoding="utf-8",
    )
    result = migrar(source, tmp_path / "out")
    assert "P-OUTER-UNION-COLUMNAS-REPETIDAS" in (
        result.carpeta / "pendientes.md"
    ).read_text(encoding="utf-8")
