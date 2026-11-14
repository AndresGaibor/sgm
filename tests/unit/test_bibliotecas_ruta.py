"""Registro y contextos para bibliotecas SAS de ruta."""

import json
from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, compile_project, project_base
from sgm.emit.plan_json import plan_to_dict
from sgm.frontend.program import analyze_program
from sgm.frontend.splitter import ZERO_WIDTH
from sgm.ir.bibliotecas import bibliotecas_de_programa, rutas_de_bibliotecas
from sgm.ir.models import Operator, Plan
from sgm.talend_item.desde_plan_contextos import GRUPOS, contextos_de_plan

ROOT = Path(__file__).resolve().parents[2]


def _items(texto: str):
    return analyze_program({"p.sas": texto}).items


def test_bibliotecas_de_programa_aplica_reemplazos_y_clear():
    items = _items(
        "LIBNAME a 'C:\\x';\nLIBNAME b IMPALA DSN=z;\nLIBNAME a CLEAR;\n"
    )

    bibliotecas = bibliotecas_de_programa(items)

    assert list(bibliotecas) == ["b"]
    assert bibliotecas["b"].motor == "impala"
    assert bibliotecas["b"].opciones == "DSN=z"


def test_rutas_de_bibliotecas_nombra_variable_de_contexto():
    bibliotecas = bibliotecas_de_programa(_items("LIBNAME datos '/d';"))

    assert rutas_de_bibliotecas(bibliotecas) == {"datos": "ruta_lib_datos"}


def test_contextos_incluyen_ruta_literal_solo_en_default():
    analysis = analyze_program(
        {"p.sas": "LIBNAME datos '/d'; DATA work.x; SET sashelp.cars; RUN;"}
    )
    plan = compile_file(analysis, "p.sas", project_base()).plan

    contextos = contextos_de_plan(plan)

    assert tuple(contextos) == GRUPOS
    assert all(
        next((p for p in grupo if p.nombre == "ruta_lib_datos"), None) is not None
        for grupo in contextos.values()
    )
    assert next(p.valor for p in contextos["Default"] if p.nombre == "ruta_lib_datos") == "/d"
    assert all(
        next(p.valor for p in grupo if p.nombre == "ruta_lib_datos") == ""
        for nombre, grupo in contextos.items()
        if nombre != "Default"
    )


def test_libname_clear_quita_la_ruta_del_plan():
    analysis = analyze_program(
        {"p.sas": "LIBNAME datos '/d'; LIBNAME datos CLEAR; DATA work.x; SET sashelp.cars; RUN;"}
    )
    plan = compile_file(analysis, "p.sas", project_base()).plan

    contextos = contextos_de_plan(plan)

    assert all(
        parametro.nombre != "ruta_lib_datos"
        for grupo in contextos.values()
        for parametro in grupo
    )


def test_ruta_de_biblioteca_no_colisiona_con_ruta_de_archivo():
    plan = Plan(program="p.sas")
    plan.graph.add_operator(
        Operator(
            "op00001",
            "unsupported",
            {"reason": "CONFIGURACION", "statement": "LIBNAME datos '/d'"},
        )
    )
    plan.graph.add_operator(
        Operator(
            "op00002",
            "read_file",
            {"datafile": "'.../entradas/x.csv'", "outputs": ["WORK.lib_datos"]},
        )
    )

    contextos = contextos_de_plan(plan)
    default = {parametro.nombre: parametro.valor for parametro in contextos["Default"]}

    assert default == {
        "ruta_lib_datos_2": ".../entradas/x.csv",
        "ruta_lib_datos": "/d",
    }


def test_ruta_dinamica_de_libname_deja_pendiente_especifico(tmp_path):
    programa = tmp_path / "p.sas"
    programa.write_text(
        'LIBNAME datos "&dir.";\nDATA work.copia; SET datos.ventas; RUN;\n',
        encoding="utf-8",
    )

    resultado = migrar(programa, tmp_path / "out")

    assert "P-LIBNAME-RUTA-DINAMICA" in {pendiente.codigo for pendiente in resultado.pendientes}
    assert not any(
        pendiente.codigo == "P-OPERADOR-SIN-SOPORTE" and "operador 'read'" in pendiente.mensaje
        for pendiente in resultado.pendientes
    )
    assert all(
        parametro.nombre != "ruta_lib_datos"
        for grupo in resultado.jobs[0].contextos.values()
        for parametro in grupo
    )


def test_casos_sin_libname_conservan_su_plan_golden():
    rel = "p0_ejemplo_basico.sas"
    ruta = ROOT / "tests/fixtures/sas" / rel
    texto = ruta.read_text(encoding="utf-8").replace(ZERO_WIDTH, "")
    compilados, _ = compile_project({rel: texto})
    actual = plan_to_dict(compilados[rel].plan)
    esperado = json.loads(
        (ROOT / "tests/golden/p0_ejemplo_basico.plan.json").read_text(encoding="utf-8")
    )

    assert actual == esperado
