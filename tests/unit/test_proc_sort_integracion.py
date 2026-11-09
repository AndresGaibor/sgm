"""Regresión de MG-P6-01: PROC SORT desde SAS hasta IR, intérprete y Job Talend."""

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.lower import lower_items
from sgm.ir.models import Column, Operator, Plan
from sgm.migrar.interprete import ejecutar_plan
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_orden import nodo_orden, nodo_unicos
from sgm.talend_item.modelo import Columna, Tabla


def _ops(text: str):
    plan = Plan(program="p.sas")
    lower_items(analyze_program({"p.sas": text}).items, plan.graph)
    return plan.graph.operators()


def _plan(text: str):
    return compile_file(analyze_program({"p.sas": text}), "p.sas", project_base()).plan


def _with_import(sort: str) -> str:
    return (
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.source DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        f"{sort}\n"
    )


def test_by_descending_se_aplica_a_cada_variable_siguiente():
    (sort,) = _ops(
        "proc sort data=source out=ordered; "
        "by descending first_key second_key descending third_key; run;"
    )

    assert sort.kind == "sort"
    assert sort.params["by"] == ["first_key", "second_key", "third_key"]
    assert sort.params["descending"] == [True, False, True]


def test_noduprec_con_by_all_se_traduce_como_unicos_por_todas_las_columnas():
    sort, dedup = _ops(
        "proc sort data=source out=unique noduprec; by _all_; run;"
    )

    assert sort.kind == "sort" and sort.params["by"] == ["_all_"]
    assert dedup.kind == "dedup" and dedup.params["by"] == ["_all_"]
    assert dedup.params["outputs"] == ["WORK.unique"]
    assert sort.status == dedup.status == "soportado"


def test_nodup_es_alias_de_noduprec_y_solo_se_acepta_con_by_all():
    sort, dedup = _ops("proc sort data=source out=unique nodup; by _all_; run;")

    assert sort.kind == "sort" and dedup.kind == "dedup"
    assert dedup.params["by"] == ["_all_"]


def test_noduprec_sin_by_all_no_elimina_filas_sin_garantizar_adyacencia():
    sort, = _ops("proc sort data=source out=ordered noduprec; by group; run;")

    assert sort.kind == "sort" and sort.status == "parcial"
    assert sort.params["outputs"] == ["WORK.ordered"]
    assert "adyacentes" in " ".join(sort.notes).lower()


def test_duput_noequals_conserva_la_ruta_de_duplicados_y_avisa_la_fila_indeterminada():
    sort, dedup = _ops(
        "proc sort data=source out=unique nodupkey dupout=duplicates noequals; "
        "by id; run;"
    )

    assert sort.params.get("descending", [False]) == [False]
    assert sort.params["equals"] is False
    assert dedup.params["outputs"] == ["WORK.unique"]
    assert dedup.params["duplicate_outputs"] == ["WORK.duplicates"]
    assert dedup.status == "parcial"
    assert "NOEQUALS" in " ".join(dedup.notes).upper()


def test_nodupkey_con_equals_no_afirma_estabilidad_de_tsortrow():
    _, dedup = _ops("proc sort data=source nodupkey; by id; run;")

    assert dedup.status == "parcial"
    assert "estabilidad de tsortrow" in " ".join(dedup.notes).lower()


def test_duput_sin_nodupkey_queda_como_hueco():
    (op,) = _ops("proc sort data=source dupout=duplicates; by id; run;")

    assert op.kind == "unsupported" and op.status == "hueco"
    assert "DUPOUT" in " ".join(op.notes).upper()


def test_duput_no_sobrescribe_dataset_de_entrada():
    (op,) = _ops(
        "proc sort data=source nodupkey dupout=source; by id; run;"
    )

    assert op.kind == "unsupported" and op.status == "hueco"
    assert "DATA=" in " ".join(op.notes)


def test_equals_y_noequals_juntos_quedan_como_hueco():
    (op,) = _ops("proc sort data=source equals noequals; by id; run;")

    assert op.kind == "unsupported" and op.status == "hueco"


def test_emisor_expande_by_all_al_esquema_de_entrada():
    op = Operator("op1", "sort", params={"by": ["_all_"], "descending": [False]})
    resultado = nodo_orden(op, [Columna("id"), Columna("value")], "tSortRow_1", 0, 1)

    criterios = next(
        parametro for parametro in resultado.nodo.parametros
        if isinstance(parametro, Tabla) and parametro.nombre == "CRITERIA"
    )
    assert criterios.celdas == (
        ("COLNAME", "id"),
        ("SORT", "alpha"),
        ("ORDER", "asc"),
        ("COLNAME", "value"),
        ("SORT", "alpha"),
        ("ORDER", "asc"),
    )


def test_emisor_conserva_descending_por_columna():
    op = Operator(
        "op1",
        "sort",
        params={"by": ["id", "value"], "descending": [True, False]},
    )
    resultado = nodo_orden(op, [Columna("id"), Columna("value")], "tSortRow_1", 0, 1)

    criterios = next(
        parametro for parametro in resultado.nodo.parametros
        if isinstance(parametro, Tabla) and parametro.nombre == "CRITERIA"
    )
    assert [criterios.celdas[i + 2][1] for i in (0, 3)] == ["desc", "asc"]


def test_emisor_noduprec_marca_todas_las_columnas_como_llave():
    op = Operator("op1", "dedup", params={"by": ["_all_"]})
    resultado = nodo_unicos(
        op, [Columna("id"), Columna("value")], "tUniqRow_1", "tSortRow_1", 0, 1
    )

    llave = next(
        parametro for parametro in resultado.nodo.parametros
        if isinstance(parametro, Tabla) and parametro.nombre == "UNIQUE_KEY"
    )
    assert llave.celdas == (
        ("SCHEMA_COLUMN", "id"),
        ("KEY_ATTRIBUTE", "true"),
        ("CASE_SENSITIVE", "true"),
        ("SCHEMA_COLUMN", "value"),
        ("KEY_ATTRIBUTE", "true"),
        ("CASE_SENSITIVE", "true"),
    )


def test_interprete_noduprec_by_all_elimina_filas_id_enticas():
    plan = _plan(_with_import("PROC SORT DATA=WORK.source OUT=WORK.unique NODUPREC; BY _ALL_; RUN;"))

    result = ejecutar_plan(
        plan,
        {
            "source": [
                {"id": "b", "value": "2"},
                {"id": "a", "value": "1"},
                {"id": "a", "value": "1"},
            ]
        },
    )

    assert result["unique"] == [
        {"id": "a", "value": "1"},
        {"id": "b", "value": "2"},
    ]


def test_duput_es_consumible_y_el_item_lo_conecta_por_la_salida_duplicate():
    text = _with_import(
        "PROC SORT DATA=WORK.source OUT=WORK.unique NODUPKEY DUPOUT=WORK.duplicates; "
        "BY id; RUN;\n"
        "PROC SORT DATA=WORK.duplicates OUT=WORK.duplicates_ordered; BY id; RUN;"
    )
    plan = _plan(text)

    result = ejecutar_plan(
        plan,
        {
            "source": [
                {"id": "2", "value": "first"},
                {"id": "1", "value": "kept"},
                {"id": "2", "value": "duplicate"},
            ]
        },
    )
    assert result["unique"] == [
        {"id": "1", "value": "kept"},
        {"id": "2", "value": "first"},
    ]
    assert result["duplicates_ordered"] == [{"id": "2", "value": "duplicate"}]

    job = plan_a_jobs(
        plan,
        {
            "work.source": [
                Column("id", "String"),
                Column("value", "String"),
            ]
        },
    ).jobs[0]
    duplicados = next(n for n in job.nodos if n.componente == "tUniqRow")
    orden = next(
        n for n in job.nodos if n.componente == "tSortRow" and n.unico != "tSortRow_1"
    )
    arista = next(
        c
        for c in job.conexiones
        if c.origen == duplicados.unico and c.destino == orden.unico
    )
    assert arista.conector == "DUPLICATE"
