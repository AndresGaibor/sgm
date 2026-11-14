"""Contexto local de Impala para Jobs con `tImpalaRow`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.catalog.config import Engines, Env, Project
from sgm.cli import app
from sgm.cli_migrar import migrar
from sgm.compile import compile_project
from sgm.seguridad.escaner_secretos import escanear_ruta
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_conexion import (
    VARIABLES_BASE,
    cargar_contexto_dev,
)
from sgm.talend_item.desde_plan_contextos import GRUPOS, contextos_de_plan
from sgm.talend_item.item import render_item

CASO = (
    Path(__file__).resolve().parents[1]
    / "corpus"
    / "L2"
    / "l2_16_sql_en_misma_base"
    / "programa.sas"
)
VALORES_DEV = {
    "impala_host": "localhost",
    "impala_puerto": "21050",
    "impala_base": "default",
    "impala_jdbc_extra": ";auth=noSasl",
}


def _plan():
    compilados, _ = compile_project(
        {CASO.name: CASO.read_text(encoding="utf-8")},
        env=Env(
            engines=Engines(),
            project=Project(placement_strategy="push_to_db", target_engine="impala"),
        ),
        library_engines={"LZ": "impala"},
    )
    return compilados[CASO.name].plan


def _parametros_timpalarow(job) -> dict[str, str]:
    filas = [nodo for nodo in job.nodos if nodo.componente == "tImpalaRow"]
    assert len(filas) == 1
    return {
        nombre: valor
        for parametro in filas[0].parametros
        if isinstance(parametro, tuple)
        for _, nombre, valor, _ in [parametro]
    }


def test_timpalarow_usa_referencias_de_contexto_sin_incrustar_hosts_ni_credenciales():
    plan = _plan()
    resultado = plan_a_jobs(plan, {}, conexion_en_contexto=True)

    parametros = _parametros_timpalarow(resultado.jobs[0])
    assert parametros["HOST"] == "context.impala_host"
    assert parametros["PORT"] == "Integer.parseInt(context.impala_puerto)"
    assert parametros["DBNAME"] == "context.impala_base"
    assert parametros["IMPALA_ADDITIONAL_JDBC"] == "context.impala_jdbc_extra"
    assert parametros["PASS"] == "((String)null)"
    assert parametros["USER"] == ""
    item = render_item(resultado.jobs[0])
    assert "localhost" not in item
    assert "sgmtest_pw_local" not in item
    assert 'name="impala_host"' in item


def test_sin_contexto_dev_conserva_los_parametros_vacios():
    parametros = _parametros_timpalarow(plan_a_jobs(_plan(), {}).jobs[0])

    assert parametros["HOST"] == parametros["PORT"] == parametros["DBNAME"] == '""'
    assert parametros["IMPALA_ADDITIONAL_JDBC"] == '""'
    assert parametros["USER"] == ""
    assert parametros["PASS"] == "((String)null)"


def test_contexto_dev_agrega_las_mismas_variables_a_cada_grupo_en_orden():
    contextos = contextos_de_plan(_plan(), dev=VALORES_DEV)

    assert tuple(contextos) == GRUPOS
    nombres = [[parametro.nombre for parametro in contextos[g]] for g in GRUPOS]
    assert all(grupo == nombres[0] for grupo in nombres)
    assert nombres[0] == ["ruta_lib_lz", *VARIABLES_BASE]
    valores_default = {p.nombre: p.valor for p in contextos["Default"]}
    valores_dev = {p.nombre: p.valor for p in contextos["DEV"]}
    assert valores_default["ruta_lib_lz"] == "/data/lz"
    assert valores_dev == {"ruta_lib_lz": "", **VALORES_DEV}
    for grupo in ("Default", "QA", "PROD"):
        valores = {p.nombre: p.valor for p in contextos[grupo]}
        valores.pop("ruta_lib_lz", None)
        assert set(valores.values()) == {""}


def test_cargar_contexto_dev_rechaza_claves_secretas_y_desconocidas(tmp_path):
    for clave in ("impala_clave", "otra_variable"):
        ruta = tmp_path / f"{clave}.json"
        ruta.write_text(json.dumps({**VALORES_DEV, clave: "dato"}), encoding="utf-8")

        with pytest.raises(ValueError):
            cargar_contexto_dev(ruta)


def test_migrar_publica_contextos_dev_y_prod_sin_hallazgos_secretos(tmp_path):
    contexto = tmp_path / "contexto.json"
    contexto.write_text(json.dumps({"_nota": "local", **VALORES_DEV}), encoding="utf-8")
    programa = tmp_path / "programa.sas"
    programa.write_text(
        "proc sql;\n"
        "execute (create table impala.destino as select 1 as id) by impala;\n"
        "quit;\n",
        encoding="utf-8",
    )

    resultado = migrar(programa, tmp_path / "out", contexto_dev=contexto)

    assert resultado.jobs, resultado.pendientes
    assert not resultado.fallo_seguridad
    assert resultado.carpeta.is_dir(), (resultado.carpeta, resultado.escritos)
    assert resultado.escritos, (resultado.carpeta, resultado.hallazgos_seguridad)
    dev = (resultado.carpeta / "contextos" / "DEV.yaml").read_text(encoding="utf-8")
    prod = (resultado.carpeta / "contextos" / "PROD.yaml").read_text(encoding="utf-8")
    assert 'valor: "localhost"' in dev
    assert 'nombre: impala_host' in prod
    assert 'valor: ""' in prod
    assert not escanear_ruta(resultado.carpeta).hallazgos


def test_cli_migrar_acepta_opcion_contexto_dev(tmp_path):
    programa = tmp_path / "programa.sas"
    programa.write_text(
        "proc sql;\n"
        "execute (create table impala.destino as select 1 as id) by impala;\n"
        "quit;\n",
        encoding="utf-8",
    )
    contexto = Path(__file__).resolve().parents[2] / "env" / "contexto_dev.json"
    salida = tmp_path / "out"

    resultado = CliRunner().invoke(
        app,
        ["migrar", str(programa), "--out", str(salida), "--contexto-dev", str(contexto)],
    )

    assert resultado.exit_code == 0, resultado.output
    dev = (salida / "programa" / "contextos" / "DEV.yaml").read_text(encoding="utf-8")
    assert 'valor: "localhost"' in dev
