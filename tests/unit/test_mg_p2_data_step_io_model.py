"""Contrato de análisis e IR para la entrada de archivos en DATA step."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.datastep import classify_statement
from sgm.frontend.program import analyze_program
from sgm.ir.models import Operator
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.passes.p10_components import choose, load_engines, load_rules

RULES = load_rules()
ENGINES = load_engines()


def _plan(text: str):
    analysis = analyze_program({"p.sas": text})
    return compile_file(analysis, "p.sas", project_base()).plan


def _archivo(plan, kind: str = "read_file") -> Operator:
    return next(op for op in plan.graph.operators() if op.kind == kind)


def test_infile_conserva_ruta_y_opciones_delimitadas():
    statement = classify_statement(
        "infile '/datos/entrada.csv' dsd dlm=',' firstobs=2 truncover lrecl=2048", 4
    )

    assert statement.kind == "infile"
    assert statement.fields["source"] == "'/datos/entrada.csv'"
    assert statement.fields["options"] == {
        "dsd": True,
        "dlm": ",",
        "firstobs": 2,
        "truncover": True,
        "lrecl": 2048,
    }


def test_input_reconoce_nombres_y_forma_de_lectura():
    examples = [
        ("input id nombre saldo", "list", ["id", "nombre", "saldo"]),
        ("input id $ 1-10 region $ 11-12 saldo 13-24", "column", ["id", "region", "saldo"]),
        ("input fecha yymmdd10. saldo comma12.2", "formatted", ["fecha", "saldo"]),
        ("input amount 12.", "formatted", ["amount"]),
        ("input amount 12.2", "formatted", ["amount"]),
        ("input amount :comma12.2", "formatted", ["amount"]),
        ("input 'nombre extendido'n valor", "unknown", []),
    ]

    for text, mode, names in examples:
        statement = classify_statement(text, 5)
        assert statement.kind == "input"
        assert statement.fields["mode"] == mode
        assert statement.fields["names"] == names
        assert statement.fields["raw"] == text


def test_infile_e_input_delimitados_quedan_acoplados_en_la_ir():
    plan = _plan(
        "data work.entrada;\n"
        "infile '/datos/entrada.txt' dlm='|' firstobs=2;\n"
        "input codigo monto;\n"
        "run;"
    )
    op = _archivo(plan)

    assert op.params["datafile"] == "'/datos/entrada.txt'"
    assert op.params["file_format"] == "delimited"
    assert op.params["delimiter"] == "|"
    assert op.params["firstobs"] == 2
    assert op.params["input_names"] == ["codigo", "monto"]


def test_nombres_de_input_se_conservan_en_el_esquema_sin_inventar_tipos():
    plan = _plan(
        "data work.entrada;\n"
        "infile '/datos/entrada.txt' dlm='|' firstobs=2;\n"
        "input codigo monto;\n"
        "run;"
    )

    esquemas, pendientes = esquemas_de_entrada(plan, {}, None)

    assert [col.name for col in esquemas["work.entrada"]] == ["codigo", "monto"]
    assert {col.type for col in esquemas["work.entrada"]} == {"String"}
    assert esquemas["work.entrada"][0].source == "sas_input"
    assert any(p.codigo == "P-TIPO-DESCONOCIDO" for p in pendientes)


def test_input_sas_prevalece_sobre_primera_fila_de_muestra(tmp_path):
    (tmp_path / "entrada.txt").write_text("A|10\nB|20\n", encoding="utf-8")
    plan = _plan(
        "data work.entrada;\n"
        "infile '/datos/entrada.txt' dlm='|';\n"
        "input codigo monto;\n"
        "run;"
    )

    esquemas, _ = esquemas_de_entrada(plan, {}, tmp_path)

    assert [col.name for col in esquemas["work.entrada"]] == ["codigo", "monto"]
    assert {col.source for col in esquemas["work.entrada"]} == {"sas_input"}


def test_entrada_posicional_se_enruta_a_componente_declarado():
    plan = _plan(
        "data work.fijos;\n"
        "infile '/datos/registros.dat' lrecl=80;\n"
        "input id $ 1-10 region $ 11-12 amount 13-24;\n"
        "run;"
    )
    op = _archivo(plan)
    found = choose(op, RULES, ENGINES)

    assert op.params["file_format"] == "positional"
    assert op.params["input_names"] == ["id", "region", "amount"]
    assert found is not None and found[1] == "tFileInputPositional"


def test_set_e_infile_en_el_mismo_data_step_quedan_bloqueados():
    plan = _plan(
        "data work.mezcla;\n"
        "set work.origen;\n"
        "infile '/datos/adicional.txt' dlm='|';\n"
        "input codigo;\n"
        "run;"
    )
    op = _archivo(plan)

    assert op.status == "hueco"
    assert op.params["reason"] == "LECTURAS_DATA_STEP_MIXTAS"
    assert op.params["input_names"] == ["codigo"]
