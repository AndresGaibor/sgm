"""PROC FORMAT reconoce mapas discretos conservadores y deja rangos pendientes."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.emit.plan_json import plan_to_dict
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column
from sgm.migrar.interprete import NoSoportadoEnInterprete, ejecutar_plan


def _plan(text: str, estado: str | None = "String"):
    context = project_base()
    if estado:
        context["schemas"] = {
            f"work.{table}": [Column("estado", estado, source="catalog")]
            for table in ("origen", "clientes")
        }
    return compile_file(analyze_program({"p.sas": text}), "p.sas", context).plan


def test_value_character_map_is_kept_in_plan_and_applied_by_reference_interpreter():
    text = """PROC FORMAT;
      VALUE $estf 'A'='Activo' 'I'='Inactivo' OTHER='Otro';
    RUN;
    DATA WORK.con_estado; SET WORK.clientes;
      desc = PUT(estado, $estf.);
    RUN;"""

    plan = _plan(text)

    [formato] = plan.formatos
    assert formato.nombre == "$estf"
    assert formato.rangos == (("A", "Activo"), ("I", "Inactivo"))
    assert formato.otro == "Otro"
    assert ejecutar_plan(
        plan,
        {
            "clientes": [
                {"id": "1", "estado": "A"},
                {"id": "2", "estado": "I"},
                {"id": "3", "estado": "X"},
                {"id": "4", "estado": ""},
                {"id": "5", "estado": "a"},
            ]
        },
    )["con_estado"] == [
        {"id": "1", "estado": "A", "desc": "Activo"},
        {"id": "2", "estado": "I", "desc": "Inactivo"},
        {"id": "3", "estado": "X", "desc": "Otro"},
        {"id": "4", "estado": "", "desc": "Otro"},
        {"id": "5", "estado": "a", "desc": "Otro"},
    ]
    assert plan_to_dict(plan)["user_formats"] == [
        {
            "nombre": "$estf",
            "rangos": [["A", "Activo"], ["I", "Inactivo"]],
            "otro": "Otro",
        }
    ]
    from sgm.ir.formatos_usuario import FormatoUsuario
    serialized = json.loads(json.dumps(plan_to_dict(plan)))["user_formats"][0]
    assert FormatoUsuario(
        serialized["nombre"], tuple(map(tuple, serialized["rangos"])), serialized["otro"]
    ) == formato
    with pytest.raises(FrozenInstanceError):
        formato.nombre = "$otro"
    with pytest.raises(NoSoportadoEnInterprete, match="tipo SAS sin demostrar"):
        ejecutar_plan(_plan(text, estado=None), {"clientes": [{"id": "6", "estado": None}]})


@pytest.mark.parametrize("separator", [" ", "\n"])
def test_value_posterior_al_put_queda_pendiente_incluso_en_la_misma_linea(separator):
    plan = _plan(separator.join([
        "DATA destino; SET origen; desc=PUT(estado,$estf.); RUN;",
        "PROC FORMAT; VALUE $estf '1'='Uno' OTHER='Otro'; RUN;",
    ]))
    with pytest.raises(NoSoportadoEnInterprete, match="P-FORMATO-NO-DISPONIBLE"):
        ejecutar_plan(plan, {"origen": [{"estado": "1"}]})


@pytest.mark.parametrize("estado", ["String", "Double", None])
def test_put_tipa_la_columna_sas_sin_inferir_desde_la_celda_csv(estado):
    plan = _plan("PROC IMPORT DATAFILE='origen.csv' OUT=origen DBMS=CSV; GETNAMES=YES; RUN; "
                 "PROC FORMAT; VALUE $estf '1'='Uno' OTHER='Otro'; RUN; "
                 "DATA destino; SET origen; desc=PUT(estado,$estf.); RUN;", estado)
    rows = {"origen": [{"estado": "1"}]}
    if estado == "String":
        assert ejecutar_plan(plan, rows)["destino"][0]["desc"] == "Uno"
    else:
        with pytest.raises(NoSoportadoEnInterprete, match="P-FORMATO-TIPO"):
            ejecutar_plan(plan, rows)


def test_l3_34_conserva_pendiente_si_proc_import_no_prueba_tipo():
    directory = Path(__file__).resolve().parents[1] / "corpus/L3/l3_34_format_value_y_put"
    plan = _plan((directory / "programa.sas").read_text(encoding="utf-8"), estado=None)
    with pytest.raises(NoSoportadoEnInterprete, match="P-FORMATO-TIPO"):
        ejecutar_plan(plan, {"clientes": [{"estado": "A"}]})


def test_numeric_ranges_stay_pending_until_d1_supports_them():
    plan = _plan("PROC FORMAT; VALUE nivel 1-5='bajo'; RUN;")

    [operador] = list(plan.graph.operators())
    assert operador.kind == "unsupported"
    assert operador.params["pending_code"] == "P-FORMATO-RANGO-SIN-SOPORTE"
    assert not plan.formatos


def test_multiple_discrete_formats_keep_separate_names():
    plan = _plan(
        "PROC FORMAT; VALUE $estado 'A'='Activo' OTHER='Otro'; "
        "VALUE $canal 'W'='Web' OTHER='Otro canal'; RUN;"
    )

    assert [(formato.nombre, formato.otro) for formato in plan.formatos] == [
        ("$estado", "Otro"),
        ("$canal", "Otro canal"),
    ]


def test_custom_put_keeps_an_emission_gap_in_talend():
    plan = _plan(
        "PROC FORMAT; VALUE $estado 'A'='Activo' OTHER='Otro'; RUN; "
        "DATA destino; SET origen; descripcion=PUT(estado, $estado.); RUN;"
    )

    [hueco] = [
        hueco for hueco in plan.gaps if "P-FORMATO-USUARIO-SIN-EMISOR" in hueco.text
    ]
    assert hueco.reason == "FUNCION_NO_MAPEADA"
    assert not any(
        candidate.get("source") == "PUT(estado, $estado.)"
        for op in plan.graph.operators()
        for candidate in op.params.get("talend_expression_candidates", [])
    )


@pytest.mark.parametrize("body", [
    "VALUE $estado 'A'='Activo' 'B'-'D'='Rango'",
    "INVALUE $estado 'A'='Activo'",
    "VALUE $estado (upcase) 'A'='Activo'",
    "VALUE $estado 'A'='Activo' OTHER=[otro.]",
])
def test_unknown_constructs_do_not_register_a_partial_format(body):
    plan = _plan(f"PROC FORMAT; {body}; RUN;")
    assert not plan.formatos
    assert all(op.status == "hueco" for op in plan.graph.operators())


def test_unknown_format_does_not_inherit_registry_from_another_plan():
    registered = _plan("PROC FORMAT; VALUE $estado 'A'='Activo'; RUN; "
                       "DATA destino; SET origen; desc=PUT(estado, $estado.); RUN;")
    assert ejecutar_plan(registered, {"origen": [{"estado": "A"}]})["destino"][0]["desc"] == "Activo"
    plan = _plan("DATA destino; SET origen; desc=PUT(estado, $estado.); RUN;")
    with pytest.raises(NoSoportadoEnInterprete):
        ejecutar_plan(plan, {"origen": [{"estado": "A"}]})


def test_registered_format_without_other_keeps_unmatched_values_explicit():
    plan = _plan("PROC FORMAT; VALUE $estado 'A'='Activo'; RUN; "
                 "DATA destino; SET origen; desc=PUT(estado, $estado.); RUN;")
    with pytest.raises(NoSoportadoEnInterprete, match="sin OTHER"):
        ejecutar_plan(plan, {"origen": [{"estado": "X"}]})


def test_custom_put_emission_publishes_specific_pending(tmp_path):
    from sgm.cli_migrar import migrar

    source = tmp_path / "p.sas"
    source.write_text("PROC FORMAT; VALUE $estado 'A'='Activo' OTHER='Otro'; RUN; "
                      "DATA destino; SET origen; desc=PUT(estado, $estado.); RUN;", encoding="utf-8")
    result = migrar(source, tmp_path / "out")
    assert "P-FORMATO-USUARIO-SIN-EMISOR" in (
        result.carpeta / "pendientes.md"
    ).read_text(encoding="utf-8")


def test_normalization_only_changes_declared_put_argument():
    from sgm.formatos.usuario import normalize_user_put

    assert normalize_user_put("PUT(upcase(estado), $estf.)", {"$estf"}) == (
        "PUT(upcase(estado), '$estf')"
    )
    for text in ["PUT(estado, $otro.)", "INPUT(estado, $estf.)", "'$estf.'",
                 "'PUT(estado, $estf.)'", "/* PUT(estado, $estf.) */", "PUT(estado, $estf. + 1)"]:
        assert normalize_user_put(text, {"$estf"}) == text


def test_range_like_text_in_a_label_is_literal():
    plan = _plan("PROC FORMAT; VALUE $r 'A'='1-5=' 'B'='L''autre'; RUN;")
    assert plan.formatos[0].rangos == (("A", "1-5="), ("B", "L'autre"))
