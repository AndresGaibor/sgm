"""Agregados explícitos de MEANS/SUMMARY, conforme proc.pdf, pp. 1555–1573."""

from __future__ import annotations

import pytest

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.interprete_base import NoSoportadoEnInterprete
from sgm.talend_item.desde_plan_agregado import nodo_agregado
from sgm.talend_item.modelo import Columna, Tabla
from sgm.talend_item.validador import validar_job


def _plan(text: str):
    return compile_file(analyze_program({"p.sas": text}), "p.sas", project_base()).plan


def _run(text: str, rows: list[dict]):
    return ejecutar_plan(_plan(text), {"ventas": rows})


ROWS = [
    {"region": "N", "monto": "10"},
    {"region": "N", "monto": None},
    {"region": "S", "monto": "5"},
    {"region": "S", "monto": "7"},
]


def test_means_nway_preserva_esquema_y_omite_faltantes():
    text = """PROC MEANS DATA=WORK.ventas NOPRINT NWAY;
    CLASS region; VAR monto;
    OUTPUT OUT=WORK.res(DROP=_TYPE_ _FREQ_) SUM=total MEAN=prom N=n; RUN;"""
    assert _run(text, ROWS)["res"] == [
        {"region": "N", "total": "10", "prom": "10", "n": "1"},
        {"region": "S", "total": "12", "prom": "6", "n": "2"},
    ]


def test_summary_global_produce_una_fila_con_nombres_de_output():
    text = """PROC SUMMARY DATA=WORK.ventas; VAR monto;
    OUTPUT OUT=WORK.tot(DROP=_TYPE_ _FREQ_) SUM=total MIN=minimo MAX=maximo N=n; RUN;"""
    assert _run(text, ROWS)["tot"] == [
        {"total": "22", "minimo": "5", "maximo": "10", "n": "3"}
    ]


def test_nmiss_y_n_tratan_cada_var_independientemente():
    text = """PROC MEANS DATA=ventas; VAR a b;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) N=na nb NMISS=ma mb MEAN=pa pb; RUN;"""
    assert _run(text, [{"a": "2", "b": None}, {"a": ".A", "b": "4"}])["res"] == [
        {"na": "1", "nb": "1", "ma": "1", "mb": "1", "pa": "2", "pb": "4"}
    ]


def test_nway_dos_clases_excluye_faltantes_de_class():
    text = """PROC MEANS DATA=ventas NWAY; CLASS region canal; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total N=n NMISS=nm; RUN;"""
    rows = [
        {"region": "N", "canal": "a", "monto": "2"},
        {"region": "N", "canal": "b", "monto": "4"},
        {"region": "N", "canal": "a", "monto": None},
        {"region": None, "canal": "a", "monto": "100"},
    ]
    assert _run(text, rows)["res"] == [
        {"region": "N", "canal": "a", "total": "2", "n": "1", "nm": "1"},
        {"region": "N", "canal": "b", "total": "4", "n": "1", "nm": "0"},
    ]


def test_todo_faltante_requiere_observacion_para_estadisticos_pero_no_n_nmiss():
    # proc.pdf, p. 122: los estadísticos no calculables son faltantes, N/NMISS no los requieren.
    text = """PROC MEANS DATA=ventas; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=s MEAN=p MIN=mi MAX=ma N=n NMISS=nm; RUN;"""
    assert _run(text, [{"monto": None}, {"monto": "."}, {"monto": ".Z"}])["res"] == [
        {"s": None, "p": None, "mi": None, "ma": None, "n": "0", "nm": "3"}
    ]


@pytest.mark.parametrize("alias", ["_type_", "_freq_"])
def test_alias_de_estadistico_eliminado_por_drop_queda_pendiente(alias):
    plan = _plan(f"""PROC MEANS DATA=ventas; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM={alias}; RUN;""")
    assert any(op.kind == "unsupported" and op.status == "hueco"
               for op in plan.graph.operators())


@pytest.mark.parametrize("procedure", ["MEANS", "SUMMARY"])
def test_std_publica_pendiente_y_no_emite_agregado_incompleto(procedure):
    plan = _plan(f"""PROC {procedure} DATA=ventas; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total STD=desvio; RUN;""")
    assert not any(op.kind == "aggregate" for op in plan.graph.operators())
    assert any(op.params.get("pending_code") == "P-MEANS-ESTADISTICO-SIN-SOPORTE"
               for op in plan.graph.operators())


def test_pendiente_conserva_data_como_entrada_sin_suponer_salida_calculada():
    plan = _plan("""PROC MEANS DATA=ventas; CLASS region; VAR monto;
    OUTPUT OUT=res SUM=total; RUN;""")
    pending = next(op for op in plan.graph.operators() if op.kind == "unsupported")
    assert pending.params.get("inputs") == ["WORK.ventas"]
    assert not pending.params.get("outputs")


def test_output_sin_estadisticos_no_sustituye_las_cinco_filas_sas_por_agregado_vacio():
    # p. 1558: sin keywords, OUTPUT entrega N/MIN/MAX/MEAN/STD; STD sigue pendiente.
    plan = _plan("PROC MEANS DATA=ventas; CLASS region; VAR monto; OUTPUT OUT=res; RUN;")
    assert not any(op.kind == "aggregate" for op in plan.graph.operators())
    pending = next(op for op in plan.graph.operators() if op.params.get("procedure") == "means")
    assert pending.params["pending_code"] == "P-MEANS-ESTADISTICO-SIN-SOPORTE"


@pytest.mark.parametrize("flags,classes,dataset", [
    ("", "", "res"),
    ("NWAY", "CLASS region;", "res"),
    ("", "CLASS region;", "res(DROP=_TYPE_ _FREQ_)"),
    ("", "", "res(DROP=_TYPE_)"),
])
def test_esquema_automatico_o_tipos_class_no_modelados_quedan_pendientes(flags, classes, dataset):
    plan = _plan(f"""PROC MEANS DATA=ventas {flags}; {classes} VAR monto;
    OUTPUT OUT={dataset} SUM=total; RUN;""")
    assert any(op.params.get("pending_code") == "P-MEANS-TYPE-NO-DEMOSTRADO"
               for op in plan.graph.operators())


@pytest.mark.parametrize("extra", ["WEIGHT monto;", "WHERE monto > 5;", "CLASS region / MISSING;"])
def test_sentencias_no_modeladas_no_se_ignoran(extra):
    plan = _plan(f"""PROC MEANS DATA=ventas NWAY; {extra} VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total; RUN;""")
    assert any(op.kind == "unsupported" and op.status == "hueco"
               for op in plan.graph.operators())


def test_sin_output_conserva_regla_declarativa():
    ops = _plan("PROC MEANS DATA=ventas; CLASS region; VAR monto; RUN;").graph.operators()
    assert any(op.kind == "aggregate" and op.params.get("class") == ["region"] for op in ops)


@pytest.mark.parametrize("case,columns,functions", [
    ("l3_30_means_class_nway", ["region", "total", "prom", "n"], ["sum", "avg", "count"]),
    ("l3_31_summary_global", ["total", "minimo", "maximo", "n"], ["sum", "min", "max", "count"]),
])
def test_corpus_emite_un_agregado_con_esquema_de_output(tmp_path, case, columns, functions):
    from pathlib import Path

    directory = Path(__file__).resolve().parents[1] / "corpus" / "L3" / case
    result = migrar(directory / "programa.sas", tmp_path / "out", muestra=directory / "entradas")
    aggregates = [node for job in result.jobs for node in job.nodos
                  if node.componente == "tAggregateRow"]
    assert len(aggregates) == 1
    schemas = aggregates[0].metadatas
    output_columns = schemas[0].columnas if schemas else aggregates[0].columnas
    assert [column.nombre for column in output_columns] == columns
    operations = next(param.celdas for param in aggregates[0].parametros
                      if isinstance(param, Tabla) and param.nombre == "OPERATIONS")
    assert [value for key, value in operations if key == "FUNCTION"] == functions
    assert [value for key, value in operations if key == "IGNORE_NULL"] == ["true"] * len(functions)
    assert not any(p.codigo.startswith("P-AGREGADO") for p in result.pendientes)
    assert all(validar_job(job) == [] for job in result.jobs)


def test_nmiss_sin_equivalencia_talend_no_emite_esquema_incompleto(tmp_path):
    source = tmp_path / "p.sas"
    (tmp_path / "ventas.csv").write_text("monto\n10\n\n", encoding="utf-8")
    source.write_text("""PROC IMPORT DATAFILE='ventas.csv' OUT=ventas DBMS=CSV REPLACE;
    GETNAMES=YES; RUN;
    PROC MEANS DATA=ventas; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total NMISS=nm; RUN;""", encoding="utf-8")
    result = migrar(source, tmp_path / "out", muestra=tmp_path)
    assert any(p.codigo == "P-AGREGADO-SIN-TRADUCIR" for p in result.pendientes)
    assert not any(node.componente == "tAggregateRow" for job in result.jobs for node in job.nodos)


def test_mean_de_var_entera_conserva_promedio_real_en_talend():
    plan = _plan("""PROC MEANS DATA=ventas; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) MEAN=prom; RUN;""")
    aggregate = next(op for op in plan.graph.operators() if op.kind == "aggregate")
    result = nodo_agregado(aggregate, [Columna("monto", "id_Integer")], "agg", 0, 1)
    assert result.pendientes == []
    assert [(col.nombre, col.tipo) for col in result.columnas] == [("prom", "id_Double")]


@pytest.mark.parametrize("procedure", ["MEANS", "SUMMARY"])
@pytest.mark.parametrize("missing", [".", "._", *[f".{letter}" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]])
def test_class_numerica_demostrada_excluye_faltantes_especiales(procedure, missing):
    text = f"""PROC {procedure} DATA=ventas NWAY; CLASS region; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total N=n; RUN;"""
    context = project_base()
    context["schemas"] = {"work.ventas": [
        Column("region", "Double", source="catalog"), Column("monto", "Double", source="catalog"),
    ]}
    plan = compile_file(analyze_program({"p.sas": text}), "p.sas", context).plan
    result = ejecutar_plan(plan, {"ventas": [
        {"region": missing, "monto": "10"}, {"region": 2, "monto": "7"},
    ]})
    assert result["res"] == [{"region": "2", "total": "7", "n": "1"}]


@pytest.mark.parametrize("procedure", ["MEANS", "SUMMARY"])
def test_class_numerica_declarada_en_codigo_excluye_punto_a(procedure):
    text = f"""DATA ventas; LENGTH region 8 monto 8; SET origen; region=region; RUN;
    PROC {procedure} DATA=ventas NWAY; CLASS region; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total N=n; RUN;"""
    plan = _plan(text)
    assert any(column.name == "region" and column.type == "Double" and column.source == "code"
               for op in plan.graph.operators() for column in op.schema or [])
    assert ejecutar_plan(plan, {"origen": [{"region": ".A", "monto": "10"}]})["res"] == []


@pytest.mark.parametrize("procedure", ["MEANS", "SUMMARY"])
@pytest.mark.parametrize("value", [".", ".A", ".Z", "._"])
def test_class_caracter_demostrada_conserva_faltantes_numericos_como_texto(procedure, value):
    text = f"""DATA ventas; LENGTH region $8 monto 8; SET origen; region=region; RUN;
    PROC {procedure} DATA=ventas NWAY; CLASS region; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total N=n; RUN;"""
    plan = _plan(text)
    assert any(column.name == "region" and column.type == "String" and column.source == "code"
               for op in plan.graph.operators() for column in op.schema or [])
    result = ejecutar_plan(plan, {"origen": [{"region": value, "monto": "10"}]})
    assert result["res"] == [{"region": value, "total": "10", "n": "1"}]


@pytest.mark.parametrize("procedure", ["MEANS", "SUMMARY"])
@pytest.mark.parametrize("value", [".", ".A", "._"])
@pytest.mark.parametrize("prefix,table", [("", "ventas"), (
    "DATA ventas; LENGTH region 8 monto 8; SET origen; RUN;", "origen"
)])
def test_class_sin_tipo_propagado_no_adivina_si_punto_a_es_faltante(
    procedure, value, prefix, table,
):
    # Sin un esquema o declaración conservada en la IR, el aspecto de '.A' no demuestra el tipo.
    text = prefix + f"""PROC {procedure} DATA=ventas NWAY; CLASS region; VAR monto;
    OUTPUT OUT=res(DROP=_TYPE_ _FREQ_) SUM=total N=n; RUN;"""
    with pytest.raises(NoSoportadoEnInterprete, match="P-MEANS-CLASS-TIPO-NO-DEMOSTRADO"):
        ejecutar_plan(_plan(text), {table: [{"region": value, "monto": "10"}]})
