"""Traducción literal y ejecución local del SQL pass-through."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from corpus_lib.caso import cargar_caso  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.models import Column, Operator  # noqa: E402
from sgm.migrar.interprete import ejecutar_plan  # noqa: E402
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete  # noqa: E402
from sgm.migrar.preparar_plan import esquemas_con_locales  # noqa: E402
from sgm.talend_item.desde_plan_paso_directo import (  # noqa: E402
    esquema_paso_directo,
    nodo_paso_directo,
)
from sgm.talend_item.jobs_diseno import java  # noqa: E402

CASE = ROOT / "tests/corpus/L0/l0_16_paso_directo_impala"
SQL = (
    "select marca, COUNT(*) as n, SUM(precio) as total\n"
    "     from sgmtest_d2.vehiculos where anio = 2026 group by marca"
)
FILAS = [
    {"marca": "Acura", "anio": "2026", "precio": "10"},
    {"marca": "Acura", "anio": "2026", "precio": "30"},
    {"marca": "Audi", "anio": "2026", "precio": "20"},
    {"marca": "Audi", "anio": "2025", "precio": "99"},
    {"marca": "BMW", "anio": "2026", "precio": "5"},
]


def _op(sql: str = SQL, engine: str = "IMPALA") -> Operator:
    return Operator(
        id="lectura",
        kind="read",
        params={"sql": sql, "engine": engine, "outputs": ["IMPALA.work.por_marca"]},
        placement=f"db:{engine.lower()}",
    )


def _parametros(nodo) -> dict[str, str]:
    return {
        fila[1]: fila[2]
        for fila in nodo.parametros
        if isinstance(fila, tuple) and len(fila) == 4
    }


def test_esquema_directo_usa_nombres_y_tipos_demostrados_por_select():
    esquema = esquema_paso_directo(
        _op(),
        {
            "sgmtest_d2.vehiculos": [
                Column("marca", "String", source="catalog"),
                Column("anio", "Long", source="catalog"),
                Column("precio", "Double", source="catalog"),
            ]
        },
    )

    assert [(col.name, col.type) for col in esquema] == [
        ("marca", "String"),
        ("n", "Long"),
        ("total", "Double"),
    ]


def test_esquema_directo_sin_catalogo_de_origen_es_vacio():
    assert esquema_paso_directo(_op(), {}) == []


def test_emisor_conserva_sql_literal_y_no_copia_dsn():
    resultado = nodo_paso_directo(
        _op(), [Column("marca", "String"), Column("n", "Long")], "tImpalaInput_1", 0, 0
    )

    assert resultado.nodo is not None
    assert resultado.nodo.componente == "tImpalaInput"
    parametros = _parametros(resultado.nodo)
    assert parametros["QUERY"] == java(SQL)
    assert parametros["USE_EXISTING_CONNECTION"] == "false"
    assert "IMPALAP" not in str(parametros)
    assert parametros["HOST"] == '""'
    assert {pendiente.codigo for pendiente in resultado.pendientes} == {"P-CONEXION-BASE"}


def test_emisor_deja_pendiente_si_no_hay_esquema():
    resultado = nodo_paso_directo(_op(), [], "tImpalaInput_1", 0, 0)

    assert resultado.nodo is None
    assert [pendiente.codigo for pendiente in resultado.pendientes] == ["P-ESQUEMA-VACIO"]


def test_emisor_no_expande_macros_del_sql_remoto():
    resultado = nodo_paso_directo(
        _op("select marca from sgmtest_d2.vehiculos where anio=&ANIO."),
        [Column("marca", "String")],
        "tImpalaInput_1",
        0,
        0,
    )

    assert resultado.nodo is None
    assert [pendiente.codigo for pendiente in resultado.pendientes] == [
        "P-PASO-DIRECTO-MACRO"
    ]


def test_emisor_indica_el_motor_no_soportado():
    resultado = nodo_paso_directo(
        _op(engine="oracle"), [Column("marca", "String")], "tOracleInput_1", 0, 0
    )

    assert resultado.nodo is None
    assert "oracle" in resultado.pendientes[0].mensaje.lower()
    assert resultado.pendientes[0].codigo == "P-MOTOR-SIN-SOPORTE"


def test_interprete_local_calcula_las_tres_marcas():
    plan = compile_file(
        analyze_program({"p.sas": CASE.joinpath("programa.sas").read_text(encoding="utf-8")}),
        "p.sas",
        project_base(),
    ).plan

    resultado = ejecutar_plan(plan, {"sgmtest_d2.vehiculos": FILAS})

    filas = sorted(resultado["por_marca"], key=lambda fila: fila["marca"])
    assert filas == [
        {"marca": "Acura", "n": 2, "total": 40},
        {"marca": "Audi", "n": 1, "total": 20},
        {"marca": "BMW", "n": 1, "total": 5},
    ]


def test_interprete_no_ejecuta_funcion_remota_no_portable():
    from sgm.migrar.interprete_paso_directo import leer

    with pytest.raises(NoSoportadoEnInterprete, match="función no portable"):
        leer(_op("select ndv(precio) as distintos from sgmtest_d2.vehiculos"),
             {"sgmtest_d2.vehiculos": FILAS})


def test_muestra_aporta_solo_el_esquema_de_entrada_al_emisor():
    plan = compile_file(
        analyze_program({"p.sas": CASE.joinpath("programa.sas").read_text(encoding="utf-8")}),
        "p.sas",
        project_base(),
    ).plan

    esquemas, pendientes = esquemas_con_locales(plan, {}, CASE / "entradas", {})

    assert [(col.name, col.type) for col in esquemas["sgmtest_d2.vehiculos"]] == [
        ("marca", None),
        ("anio", None),
        ("precio", None),
    ]
    assert pendientes == []


def test_migracion_emite_lector_con_sql_literal_usando_muestra(tmp_path):
    caso = cargar_caso(CASE)

    resultado = migrar(caso.programa, tmp_path / "out", muestra=caso.entradas)

    nodos = [nodo for job in resultado.jobs for nodo in job.nodos]
    lector = next(nodo for nodo in nodos if nodo.componente == "tImpalaInput")
    assert _parametros(lector)["QUERY"] == java(SQL)
    assert "P-CONEXION-BASE" in {item.codigo for item in resultado.pendientes}
    assert "P-ESQUEMA-VACIO" not in {item.codigo for item in resultado.pendientes}
    assert "P-FALLO-INTERNO" not in {item.codigo for item in resultado.pendientes}


def test_migracion_sin_muestra_conserva_pendiente_de_esquema(tmp_path):
    resultado = migrar(CASE / "programa.sas", tmp_path / "out")

    assert "P-ESQUEMA-VACIO" in {item.codigo for item in resultado.pendientes}
    assert not any(
        nodo.componente == "tImpalaInput" for job in resultado.jobs for nodo in job.nodos
    )


def test_caso_cubierto_coincide_con_csv_esperado():
    caso = cargar_caso(CASE)
    plan = compile_file(
        analyze_program({"p.sas": caso.programa.read_text(encoding="utf-8")}),
        "p.sas",
        project_base(),
    ).plan
    with (caso.entradas / "sgmtest_d2.vehiculos.csv").open(
        encoding="utf-8", newline=""
    ) as archivo:
        entrada = list(csv.DictReader(archivo))
    with (caso.esperado / "por_marca.csv").open(encoding="utf-8", newline="") as archivo:
        esperado = list(csv.DictReader(archivo))

    salida = ejecutar_plan(plan, {"sgmtest_d2.vehiculos": entrada})["por_marca"]

    def normalizar(rows):
        return sorted(
            [(fila["marca"], int(fila["n"]), int(float(fila["total"]))) for fila in rows]
        )

    assert normalizar(salida) == normalizar(esperado)
