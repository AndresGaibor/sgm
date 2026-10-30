"""Configuración de `env/`: validación de cada archivo y efecto de los `%include` externos."""

import json
from pathlib import Path

import pytest

from sgm.catalog.config import (
    ConfigError,
    load_env,
    parse_engines,
    parse_externals,
    parse_project,
)
from sgm.compile import compile_project

ROOT = Path(__file__).resolve().parents[2]
INCLUDE_LEJANO = '%include "/data/Programas_SAS/activenodelzcode.sas";\n'
PROGRAMA = INCLUDE_LEJANO + "data work.salida; set work.entrada; run;\n"


def _gaps(compiled: dict) -> list[str]:
    return [g.reason for result in compiled.values() for g in result.plan.gaps]


def test_engines_del_repositorio_se_cargan_y_mapean_esquemas_a_impala():
    env = load_env(ROOT / "env")
    assert env.engines.dsn["IMPALAC"] == "impala"
    libs = env.engines.library_engines()
    assert libs["PROCESO_VSPC_FINANZAS"] == "impala"
    assert libs["S_CANALES"] == "impala"


def test_project_del_repositorio_declara_la_estrategia_de_ubicacion():
    env = load_env(ROOT / "env")
    assert env.project.placement_strategy == "push_to_db"
    assert env.project.reports == "discard"
    assert env.project.max_components_per_job == 200


def test_externals_del_repositorio_declara_m_ambiente_como_contexto():
    env = load_env(ROOT / "env")
    spec = env.externals["activenodelzcode.sas"]
    assert spec.defines == ("m_ambiente",)
    assert spec.as_context is True


def test_archivo_ausente_usa_valores_por_defecto(tmp_path):
    env = load_env(tmp_path)
    assert env.engines.library_engines() == {}
    assert env.project.placement_strategy == "flow"
    assert env.externals == {}


def test_motor_con_forma_incorrecta_falla_con_el_campo():
    with pytest.raises(ConfigError, match="dsn.IMPALA"):
        parse_engines({"dsn": {"IMPALA": "Impala!"}})


def test_campo_desconocido_en_engines_falla():
    with pytest.raises(ConfigError, match="campos desconocidos"):
        parse_engines({"dsn": {}, "contrasena": "x"})


def test_estrategia_desconocida_en_project_falla():
    with pytest.raises(ConfigError, match="placement_strategy"):
        parse_project({"placement_strategy": "todo_en_la_base"})


def test_reports_fuera_de_la_lista_falla():
    with pytest.raises(ConfigError, match="reports"):
        parse_project({"reports": "pdf"})


@pytest.mark.parametrize("valor", [0, -3, True, "200"])
def test_max_components_debe_ser_entero_positivo(valor):
    with pytest.raises(ConfigError, match="max_components_per_job"):
        parse_project({"max_components_per_job": valor})


def test_externals_no_admite_rutas_ni_tipos_raros():
    with pytest.raises(ConfigError, match="solo el nombre"):
        parse_externals({"/data/x.sas": {"defines": []}})
    with pytest.raises(ConfigError, match="as_context"):
        parse_externals({"x.sas": {"as_context": "si"}})
    with pytest.raises(ConfigError, match="defines"):
        parse_externals({"x.sas": {"defines": ["m ambiente"]}})


def test_json_mal_formado_falla_con_el_nombre_del_archivo(tmp_path):
    (tmp_path / "project.json").write_text("{ no es json", encoding="utf-8")
    with pytest.raises(ConfigError, match="project.json"):
        load_env(tmp_path)


def test_include_declarado_no_genera_hueco_y_sus_variables_son_contexto(tmp_path):
    env = load_env(ROOT / "env")
    compiled, _ = compile_project({"p.sas": PROGRAMA}, env=env)
    assert "INCLUDE_EXTERNO" not in _gaps(compiled)
    plan = compiled["p.sas"].plan
    assert plan.jobs[0].contexts["m_ambiente"]["origen"].startswith("%include activenodelzcode.sas")
    assert any("activenodelzcode.sas" in nm.what for nm in plan.not_migrated)


def test_include_no_declarado_sigue_siendo_hueco():
    compiled, _ = compile_project({"p.sas": '%include "/otro/destino/x.sas";\n'})
    assert "INCLUDE_EXTERNO" in _gaps(compiled)


def test_include_declarado_sin_as_context_queda_parcial():
    env = load_env(ROOT / "env")
    env.externals["activenodelzcode.sas"] = parse_externals(
        {"activenodelzcode.sas": {"defines": ["m_ambiente"], "as_context": False}}
    )["activenodelzcode.sas"]
    compiled, _ = compile_project({"p.sas": PROGRAMA}, env=env)
    assert "INCLUDE_EXTERNO" not in _gaps(compiled)
    assert not compiled["p.sas"].plan.jobs[0].contexts


def test_archivo_presente_en_externals_se_lee_como_fuente():
    externo = {"externals/activenodelzcode.sas": "data work.desde_externo; set work.origen; run;\n"}
    env = load_env(ROOT / "env")
    env.external_files = externo
    compiled, analysis = compile_project({"p.sas": PROGRAMA}, env=env)
    outputs = [str(i.item.outputs) for i in analysis.items if hasattr(i.item, "outputs")]
    assert any("desde_externo" in o for o in outputs)
    assert "INCLUDE_EXTERNO" not in _gaps(compiled)


def test_archivo_externo_no_es_un_programa_propio():
    env = load_env(ROOT / "env")
    env.external_files = {"externals/activenodelzcode.sas": "%let x = 1;\n"}
    compiled, _ = compile_project({"p.sas": PROGRAMA}, env=env)
    assert list(compiled) == ["p.sas"]


def test_engines_json_sin_dsn_usa_el_defecto(tmp_path):
    (tmp_path / "engines.json").write_text(json.dumps({"libraries": {"lz": "impala"}}))
    env = load_env(tmp_path)
    assert env.engines.library_engines() == {"LZ": "impala"}
