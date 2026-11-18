"""Límites y esquemas de OUTER UNION CORR encontrados en la revisión de 277n."""

from __future__ import annotations

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.talend_item.validador import validar_job


def _plan(query):
    text = f"PROC SQL; CREATE TABLE WORK.r AS {query}; QUIT;"
    return compile_file(analyze_program({"p.sas": text}), "p.sas", project_base()).plan


def _pending(query, code):
    plan = _plan(query)
    unsupported = [op for op in plan.graph.operators() if op.kind == "unsupported"]
    assert len(unsupported) == 1
    assert unsupported[0].params.get("pending_code") == code
    assert not any(op.kind == "union" for op in plan.graph.operators())


def _migrate(tmp_path, query, right_id="3"):
    inputs = tmp_path / "entradas"
    inputs.mkdir()
    (inputs / "a.csv").write_text("id,x\n1,10\n2,20\n", encoding="utf-8")
    (inputs / "b.csv").write_text(f"id,y\n{right_id},30\n", encoding="utf-8")
    source = tmp_path / "p.sas"
    source.write_text(
        "PROC IMPORT DATAFILE='.../a.csv' OUT=WORK.a DBMS=CSV REPLACE; GETNAMES=YES; RUN;\n"
        "PROC IMPORT DATAFILE='.../b.csv' OUT=WORK.b DBMS=CSV REPLACE; GETNAMES=YES; RUN;\n"
        f"PROC SQL; CREATE TABLE WORK.r AS {query}; QUIT;\n"
        "PROC EXPORT DATA=WORK.r OUTFILE='.../r.csv' DBMS=CSV REPLACE; RUN;\n",
        encoding="utf-8",
    )
    return migrar(source, tmp_path / "out", muestra=inputs)


def test_qualified_star_is_pending_instead_of_a_fictional_column():
    _pending(
        "SELECT a.* FROM a OUTER UNION CORR SELECT id,y FROM b",
        "P-OUTER-UNION-CORR-SIN-SOPORTE",
    )


def test_shared_name_with_incompatible_types_does_not_emit_a_union(tmp_path):
    result = _migrate(
        tmp_path, "SELECT id,x FROM a OUTER UNION CORR SELECT id,y FROM b", right_id="texto"
    )
    assert any(p.codigo == "P-UNION-TIPO-CONFLICTO" for p in result.pendientes)
    assert not any(node.componente == "tUnite" for job in result.jobs for node in job.nodos)


def test_grouped_branch_keeps_declared_select_order_in_the_union_schema(tmp_path):
    result = _migrate(
        tmp_path, "SELECT COUNT(*) AS n,id FROM a GROUP BY id "
        "OUTER UNION CORR SELECT id,y FROM b"
    )
    assert result.pendientes == []
    assert result.jobs
    assert all(validar_job(job) == [] for job in result.jobs)
    [union] = [n for job in result.jobs for n in job.nodos if n.componente == "tUnite"]
    assert [c.nombre for c in union.metadatas[0].columnas] == ["n", "id", "y"]


def test_repeated_name_without_corr_has_priority_over_distinct_limit():
    _pending(
        "SELECT DISTINCT id FROM a OUTER UNION SELECT id FROM b",
        "P-OUTER-UNION-COLUMNAS-REPETIDAS",
    )


def test_extracted_existence_subquery_stays_pending_inside_corr():
    _pending(
        "SELECT id,x FROM a WHERE id IN (SELECT id FROM c) "
        "OUTER UNION CORR SELECT id,y FROM b",
        "P-OUTER-UNION-CORR-SIN-SOPORTE",
    )
