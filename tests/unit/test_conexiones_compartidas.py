"""Conexiones SQL compartidas por alias y parámetros de contexto sin secretos."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column
from sgm.migrar.interprete import ejecutar_plan
from sgm.seguridad.escaner_secretos import escanear_ruta
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_conexion import cargar_contexto_dev
from sgm.talend_item.desde_plan_conexiones import conexiones_de_plan, variables_de_motor
from sgm.talend_item.desde_plan_contextos import GRUPOS, contextos_de_plan

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "tests/corpus/L0/l0_17_paso_directo_postgres"
VARIABLES_POSTGRES = ("pg_host", "pg_puerto", "pg_base")
VALORES_DEV = {
    "impala_host": "impala.test.invalid",
    "impala_puerto": "21050",
    "impala_base": "sgmtest",
    "impala_jdbc_extra": "",
    "pg_host": "postgres.test.invalid",
    "pg_puerto": "5432",
    "pg_base": "sgmtest",
}


def _plan(source: str):
    analysis = analyze_program({"p.sas": source})
    return compile_file(analysis, "p.sas", project_base()).plan


def _conexiones_impala():
    source = """PROC SQL;
CONNECT TO IMPALA AS c1 (DSN=IMPALAP);
EXECUTE (select 1) BY c1;
CREATE TABLE WORK.resumen AS SELECT * FROM CONNECTION TO c1
(select marca from sgmtest_d2.vehiculos);
DISCONNECT FROM c1;
QUIT;"""
    return _plan(source)


def _parametros(nodo) -> dict[str, str]:
    return {
        fila[1]: fila[2]
        for fila in nodo.parametros
        if isinstance(fila, tuple) and len(fila) == 4
    }


def test_alias_compartido_usa_una_conexion_y_las_mismas_variables():
    plan = _conexiones_impala()

    [conexion] = conexiones_de_plan(plan)
    assert (conexion.alias, conexion.motor) == ("c1", "impala")
    assert conexion.variables == (
        "impala_host",
        "impala_puerto",
        "impala_base",
        "impala_jdbc_extra",
    )

    jobs = plan_a_jobs(
        plan,
        {
            "sgmtest_d2.vehiculos": [Column("marca", "String", source="catalog")],
        },
        conexion_en_contexto=True,
    )
    nodos = {nodo.componente: nodo for nodo in jobs.jobs[0].nodos}
    assert {"tImpalaRow", "tImpalaInput"} <= nodos.keys()
    filas = [_parametros(nodos[nombre]) for nombre in ("tImpalaRow", "tImpalaInput")]
    assert all(parametros["HOST"] == "context.impala_host" for parametros in filas)
    assert all(parametros["PORT"] == "Integer.parseInt(context.impala_puerto)" for parametros in filas)
    assert all(parametros["DBNAME"] == "context.impala_base" for parametros in filas)
    assert all(parametros["IMPALA_ADDITIONAL_JDBC"] == "context.impala_jdbc_extra" for parametros in filas)


def test_dos_motores_comparten_siete_variables_en_los_cuatro_contextos():
    plan = _plan("""PROC SQL;
CONNECT TO IMPALA AS c1;
EXECUTE (select 1) BY c1;
CONNECT TO POSTGRES AS p1;
EXECUTE (select 1) BY p1;
QUIT;""")

    conexiones = conexiones_de_plan(plan)
    assert [(conexion.alias, conexion.motor) for conexion in conexiones] == [
        ("c1", "impala"),
        ("p1", "postgres"),
    ]
    contextos = contextos_de_plan(plan, dev=VALORES_DEV)
    assert tuple(contextos) == GRUPOS
    nombres = [[parametro.nombre for parametro in contextos[grupo]] for grupo in GRUPOS]
    esperadas = [
        "impala_host",
        "impala_puerto",
        "impala_base",
        "impala_jdbc_extra",
        *VARIABLES_POSTGRES,
    ]
    assert all(nombres_grupo == esperadas for nombres_grupo in nombres)
    assert {p.nombre: p.valor for p in contextos["DEV"]} == VALORES_DEV
    for grupo in ("Default", "QA", "PROD"):
        assert {p.valor for p in contextos[grupo]} == {""}


def test_migracion_postgres_no_incrusta_opciones_y_redacta_password(tmp_path):
    resultado = migrar(
        CASE / "programa.sas",
        tmp_path / "out",
        muestra=CASE / "entradas",
        contexto_dev=ROOT / "env/contexto_dev_postgres.json",
    )

    assert resultado.carpeta.is_dir()
    item = next(resultado.carpeta.rglob("*.item")).read_text(encoding="utf-8")
    assert "sgmtest" not in item
    assert "localhost" not in item
    xml = ElementTree.fromstring(item)
    assert all(
        not parametro.get("value")
        for parametro in xml.iter("elementParameter")
        if parametro.get("field") == "PASSWORD"
    )
    pendientes = {pendiente.codigo: pendiente.mensaje for pendiente in resultado.pendientes}
    assert "P-CONEXION-OPCIONES" in pendientes
    assert "SERVER=localhost" in pendientes["P-CONEXION-OPCIONES"]
    assert "DATABASE=sgmtest" in pendientes["P-CONEXION-OPCIONES"]
    assert "PASSWORD='***'" in pendientes["P-CONEXION-OPCIONES"]
    assert "P-COMPONENTE-SIN-PLANTILLA" in pendientes
    assert not escanear_ruta(resultado.carpeta).hallazgos
    dev = (resultado.carpeta / "contextos/DEV.yaml").read_text(encoding="utf-8")
    prod = (resultado.carpeta / "contextos/PROD.yaml").read_text(encoding="utf-8")
    assert 'nombre: pg_host' in dev and 'valor: "localhost"' in dev
    assert 'nombre: pg_base' in prod and 'valor: ""' in prod


def test_contexto_postgres_no_contiene_credenciales():
    ruta = ROOT / "env/contexto_dev_postgres.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))

    assert datos == {
        "_nota": "Fixture sintética de desarrollo; no contiene credenciales.",
        "pg_host": "localhost",
        "pg_puerto": "5432",
        "pg_base": "sgmtest",
    }
    assert cargar_contexto_dev(ruta) == {
        "pg_host": "localhost",
        "pg_puerto": "5432",
        "pg_base": "sgmtest",
    }


def test_interprete_postgres_local_coincide_con_salida_sintetica():
    plan = _plan((CASE / "programa.sas").read_text(encoding="utf-8"))
    with (CASE / "entradas/public.cuentas.csv").open(encoding="utf-8", newline="") as entrada:
        entradas = list(csv.DictReader(entrada))
    with (CASE / "esperado/activos.csv").open(encoding="utf-8", newline="") as esperado:
        filas_esperadas = list(csv.DictReader(esperado))

    resultado = ejecutar_plan(plan, {"public.cuentas": entradas})

    assert resultado["activos"] == filas_esperadas


def test_variables_de_motor_rechaza_motores_desconocidos():
    with pytest.raises(ValueError, match="oracle"):
        variables_de_motor("oracle")
