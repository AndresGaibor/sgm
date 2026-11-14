"""Reconocimiento de LIBNAME y resolución segura de bibliotecas permanentes."""

import csv
from pathlib import Path
from xml.etree import ElementTree

import pytest
from typer.testing import CliRunner

from sgm.cli import app
from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.libnames import info_libname
from sgm.frontend.program import analyze_program
from sgm.frontend.steps_tipos import Libname
from sgm.ir.bibliotecas import cargar_decisiones_libnames, resolver_biblioteca
from sgm.migrar.interprete import ejecutar_plan
from sgm.seguridad.escaner_secretos import escanear_ruta

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "corpus/L0/l0_18_libname_base"


def _libname(text: str) -> Libname:
    analysis = analyze_program({"p.sas": text})
    return next(item.item for item in analysis.items if isinstance(item.item, Libname))


def test_libname_de_base_sin_decision_deja_pendiente_explicito(tmp_path):
    programa = tmp_path / "p.sas"
    programa.write_text(
        "LIBNAME lz IMPALA DSN=IMPALAP SCHEMA=sgmtest_d2;\n"
        "DATA WORK.caros; SET lz.vehiculos; WHERE precio > 15; RUN;\n"
        "LIBNAME lz CLEAR;\n",
        encoding="utf-8",
    )

    resultado = migrar(programa, tmp_path / "out")

    pendientes = [pendiente for pendiente in resultado.pendientes if pendiente.codigo == "P-LIBNAME-BASE"]
    assert len(pendientes) == 1
    assert pendientes[0].linea == 2
    assert "decisión" in pendientes[0].mensaje.lower()
    assert {pendiente.codigo for pendiente in resultado.pendientes} == {"P-LIBNAME-BASE"}


def test_fixture_l0_de_libname_tiene_decision_y_datos_sinteticos():
    assert (CASE / "decisiones.yaml").is_file()
    assert (CASE / "entradas/sgmtest_d2.vehiculos.csv").is_file()
    assert (CASE / "esperado/caros.csv").is_file()


def test_info_libname_reconoce_motor_ruta_y_clear_y_redacta_secretos():
    base = info_libname(_libname("libname lz IMPALA DSN=IMPALAP SCHEMA=foo;"))
    ruta = info_libname(_libname("libname datos 'C:\\datos';"))
    secreto = info_libname(_libname("libname x POSTGRES password=abc123;"))
    clear = info_libname(_libname("libname _all_ clear;"))

    assert (base.nombre, base.motor, base.ruta) == ("lz", "impala", None)
    assert "DSN=IMPALAP" in base.opciones
    assert (ruta.nombre, ruta.motor, ruta.ruta) == ("datos", None, "C:\\datos")
    assert (secreto.motor, secreto.opciones) == ("postgres", "password=***")
    assert "abc123" not in repr(secreto)
    assert (clear.nombre, clear.opciones) == ("_all_", "clear")


def test_resolver_libname_solo_usa_motor_y_base_de_la_decision():
    info = info_libname(_libname("libname lz IMPALA SCHEMA=valor_ignorado;"))
    bibliotecas = {"lz": info}
    decisiones = {"lz": {"motor": "impala", "base": "base_declarada"}}

    assert resolver_biblioteca("lz.vehiculos", bibliotecas, decisiones) == (
        "impala",
        "base_declarada.vehiculos",
    )
    assert resolver_biblioteca("lz.vehiculos", bibliotecas, {}) is None
    with pytest.raises(ValueError, match="no coincide"):
        resolver_biblioteca(
            "lz.vehiculos", bibliotecas, {"lz": {"motor": "postgres", "base": "db"}}
        )
    with pytest.raises(ValueError, match="identificador SQL"):
        resolver_biblioteca(
            "lz.vehiculos", bibliotecas, {"lz": {"motor": "impala", "base": "db;drop"}}
        )


def test_decisiones_libnames_rechaza_claves_que_podrian_guardar_secretos(tmp_path):
    ruta = tmp_path / "p.libnames.yaml"
    ruta.write_text(
        "libnames:\n  lz:\n    motor: impala\n    base: datos\n    password: secreto-ficticio\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="motor y base") as error:
        cargar_decisiones_libnames(ruta)
    assert "secreto-ficticio" not in str(error.value)


def test_migracion_con_decision_emite_lector_impala_y_no_incrusta_opciones(tmp_path):
    decisiones = cargar_decisiones_libnames(CASE / "decisiones.yaml")
    resultado = migrar(
        CASE / "programa.sas",
        tmp_path / "out",
        muestra=CASE / "entradas",
        libnames_decision=CASE / "decisiones.yaml",
    )

    assert resultado.jobs
    item = next(resultado.carpeta.rglob("*.item")).read_text(encoding="utf-8")
    xml = ElementTree.fromstring(item)
    parametros = {
        elemento.get("name"): elemento.get("value")
        for elemento in xml.iter("elementParameter")
    }
    assert "SELECT * FROM sgmtest_d2.vehiculos" in (parametros.get("QUERY") or "")
    assert "DSN=IMPALAP" not in item
    assert "abc123" not in item
    assert parametros["HOST"] == "context.impala_host"
    assert "P-LIBNAME-BASE" not in {p.codigo for p in resultado.pendientes}
    assert "P-CONEXION-OPCIONES" in {p.codigo for p in resultado.pendientes}
    dev_context = (resultado.carpeta / "contextos/DEV.yaml").read_text(encoding="utf-8")
    assert 'nombre: impala_host' in dev_context
    assert 'valor: ""' in dev_context
    assert not escanear_ruta(resultado.carpeta).hallazgos

    source = (CASE / "programa.sas").read_text(encoding="utf-8")
    plan = compile_file(
        analyze_program({"programa.sas": source}),
        "programa.sas",
        project_base(),
        libname_decisions=decisiones,
    ).plan
    with (CASE / "entradas/sgmtest_d2.vehiculos.csv").open(
        encoding="utf-8", newline=""
    ) as archivo:
        filas = list(csv.DictReader(archivo))
    with (CASE / "esperado/caros.csv").open(encoding="utf-8", newline="") as archivo:
        esperadas = list(csv.DictReader(archivo))

    assert ejecutar_plan(plan, {"sgmtest_d2.vehiculos": filas})["caros"] == esperadas


def test_cli_migrar_admite_archivo_libnames_explicito(tmp_path):
    resultado = CliRunner().invoke(
        app,
        [
            "migrar",
            str(CASE / "programa.sas"),
            "--out",
            str(tmp_path / "out"),
            "--muestra",
            str(CASE / "entradas"),
            "--libnames",
            str(CASE / "decisiones.yaml"),
        ],
    )

    assert resultado.exit_code == 0, resultado.output
    assert "0 Job(s)" not in resultado.output
