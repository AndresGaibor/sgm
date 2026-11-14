"""Semántica verificable de PROC APPEND y de la base que modifica."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Operator
from sgm.migrar.interprete import ejecutar_plan
from sgm.talend_item.desde_plan_union import nodo_union
from sgm.talend_item.modelo import Columna

APPEND_SAMPLE = """
proc import datafile='acum.csv' out=work.acum dbms=csv; run;
proc import datafile='n1.csv' out=work.n1 dbms=csv; run;
proc import datafile='n2.csv' out=work.n2 dbms=csv; run;
proc append base=work.acum data=work.n1; run;
proc append base=work.acum data=work.n2; run;
proc append base=work.otra data=work.n1; run;
proc append base=work.otra data=work.n2; run;
"""


def _compile(text: str):
    return compile_file(analyze_program({"programa.sas": text}), "programa.sas", project_base())


def test_append_publica_base_y_encadena_sus_versiones():
    graph = _compile(APPEND_SAMPLE).plan.graph
    appends = [op for op in graph.operators() if op.origin == "proc_append"]

    assert [op.kind for op in appends] == ["union", "union", "map", "union"]
    assert [op.params["outputs"] for op in appends] == [
        ["WORK.acum"],
        ["WORK.acum"],
        ["WORK.otra"],
        ["WORK.otra"],
    ]
    assert [
        edge.dataset
        for edge in graph.edges()
        if edge.src == appends[0].id and edge.dst == appends[1].id
    ] == ["WORK.acum@v2"]
    assert any(
        edge.src == appends[1].id and edge.dataset == "WORK.acum@v3"
        for edge in graph.edges()
    )
    assert any(
        edge.src == appends[2].id
        and edge.dst == appends[3].id
        and edge.dataset == "WORK.otra"
        for edge in graph.edges()
    )
    assert any(
        op.kind == "write" and op.params["dataset"] == "WORK.acum@v3"
        for op in graph.operators()
    )
    assert any(
        op.kind == "write" and op.params["dataset"] == "WORK.otra@v2"
        for op in graph.operators()
    )


def test_append_repetido_y_base_nueva_conservan_filas_y_orden():
    plan = _compile(APPEND_SAMPLE).plan

    outputs = ejecutar_plan(
        plan,
        {
            "acum": [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}],
            "n1": [{"id": 3, "v": "c"}],
            "n2": [{"id": 4, "v": "d"}, {"id": 5, "v": "e"}],
        },
    )

    assert outputs["acum"] == [
        {"id": 1, "v": "a"},
        {"id": 2, "v": "b"},
        {"id": 3, "v": "c"},
        {"id": 4, "v": "d"},
        {"id": 5, "v": "e"},
    ]
    assert outputs["otra"] == [
        {"id": 3, "v": "c"},
        {"id": 4, "v": "d"},
        {"id": 5, "v": "e"},
    ]


def test_append_en_macro_estatico_encadena_las_iteraciones_expandidas():
    texto = """
    proc import datafile='acum.csv' out=work.acum dbms=csv; run;
    proc import datafile='n1.csv' out=work.n1 dbms=csv; run;
    proc import datafile='n2.csv' out=work.n2 dbms=csv; run;
    %let repeticiones=2;
    %macro anexar;
      %do i=1 %to &repeticiones.;
        proc append base=work.acum data=work.n&i; run;
      %end;
    %mend;
    %anexar;
    """
    graph = _compile(texto).plan.graph
    appends = [op for op in graph.operators() if op.origin == "proc_append"]

    assert len(appends) == 2
    assert [op.kind for op in appends] == ["union", "union"]
    assert [op.params["outputs"] for op in appends] == [
        ["WORK.acum"],
        ["WORK.acum"],
    ]
    assert any(
        edge.src == appends[0].id
        and edge.dst == appends[1].id
        and edge.dataset == "WORK.acum@v2"
        for edge in graph.edges()
    )


def test_append_con_columna_solo_en_data_queda_pendiente_especifico():
    op = Operator(
        id="op00001",
        kind="union",
        params={"sources": ["WORK.base", "WORK.nuevos"], "all": True},
        origin="proc_append",
    )

    result = nodo_union(
        op,
        [
            [Columna("id"), Columna("valor")],
            [Columna("id"), Columna("valor"), Columna("extra")],
        ],
        "tUnite_1",
        0,
        7,
    )

    assert result.nodo is None
    assert [pending.codigo for pending in result.pendientes] == [
        "P-APPEND-COLUMNAS-DISTINTAS"
    ]


def test_append_con_tipo_distinto_queda_pendiente_sin_force():
    op = Operator(
        id="op00001",
        kind="union",
        params={"sources": ["WORK.base", "WORK.nuevos"], "all": True},
        origin="proc_append",
    )

    result = nodo_union(
        op,
        [
            [Columna("id", "id_Integer")],
            [Columna("id", "id_String")],
        ],
        "tUnite_1",
        0,
        7,
    )

    assert result.nodo is None
    assert [pending.codigo for pending in result.pendientes] == [
        "P-APPEND-ATRIBUTOS-DISTINTOS"
    ]


def test_append_sobre_base_permanente_sin_lectura_queda_pendiente():
    graph = _compile("proc append base=LIB_EXISTENTE.tabla data=work.n1; run;").plan.graph

    (pending,) = [op for op in graph.operators() if op.kind == "unsupported"]

    assert pending.params["pending_code"] == "P-APPEND-BASE-EXTERNA-SIN-FUENTE"
    assert "proc.pdf, p. 639" in pending.notes[0]
