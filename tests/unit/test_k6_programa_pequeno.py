"""Caso reproducible del programa pequeño con datos SASHELP sintéticos."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.csv_tabla import leer_csv  # noqa: E402
from corpus_lib.esperado_interprete import calcular  # noqa: E402
from datos_sinteticos.cars import MARCAS  # noqa: E402
from rebanar_programa import armar, leer_rebanada, verificar  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402

CASO = REPO / "tests/corpus_reales/L8/k6_cars_ciclo_append"
FUENTE = REPO / "tests/fixtures/sas/client/client_poc.sas"
ENTRADA = REPO / "tests/fixtures/datos/sashelp/cars.csv"


def test_rebanada_k6_conserva_fuente_hash_y_sustitucion_de_repeticiones():
    rebanada = leer_rebanada(CASO / "rebanada.yaml")
    with FUENTE.open(encoding="utf-8", newline="") as archivo:
        texto_fuente = archivo.read()

    assert rebanada.fuente == "tests/fixtures/sas/client/client_poc.sas"
    assert rebanada.rangos == ((12, 120),)
    assert rebanada.prologo == "%let repeticiones = 15;"
    assert rebanada.sustituciones == (
        ("%do i=1 %to 15;", "%do i=1 %to &repeticiones.;"),
    )
    assert verificar(rebanada, REPO) == []
    assert (CASO / "programa.sas").read_bytes() == armar(
        rebanada, texto_fuente
    ).encode("utf-8")


def test_entrada_cars_es_la_fixture_sintetica_versionada():
    entrada = CASO / "entradas/cars.csv"
    assert entrada.read_bytes() == ENTRADA.read_bytes()
    columnas, filas = leer_csv(entrada)

    assert columnas[0] == "Make"
    assert Counter(fila[0] for fila in filas) == MARCAS


def test_caso_declara_el_alcance_parcial_y_esperados_directos():
    caso = cargar_caso(CASO)
    columnas, filas = leer_csv(CASO / "entradas/cars.csv")
    assert caso.estado == "parcial"
    assert caso.capa == "C"
    assert caso.salidas == ("ACURA", "JAGUAR", "BMW", "CHEVROLET")
    assert "P-APPEND-MISMA-TABLA" in " ".join(caso.extra["supuestos"])
    assert "repeticiones = 3" in (caso.motivo or "")

    for marca, salida in (
        ("Acura", "ACURA"),
        ("Jaguar", "JAGUAR"),
        ("BMW", "BMW"),
        ("Chevrolet", "CHEVROLET"),
    ):
        ruta = caso.esperado / f"{salida}.csv"
        assert ruta.is_file()
        columnas_esperado, filas_esperado = leer_csv(ruta)
        base = Counter(tuple(fila) for fila in filas if fila[0] == marca)
        esperado = Counter(tuple(fila) for fila in filas_esperado)
        assert columnas_esperado == columnas
        assert len(filas_esperado) == MARCAS[marca] * 2**3
        assert esperado == Counter({fila: cantidad * 2**3 for fila, cantidad in base.items()})


def test_anillo_a_no_convierte_count_sin_alias_en_fallo_interno(tmp_path):
    resultado = migrar(
        CASO / "programa.sas",
        tmp_path / "salida",
        tablas_locales=REPO / "env/tablas_locales.json",
    )

    assert not [p for p in resultado.pendientes if p.codigo == "P-FALLO-INTERNO"]


@pytest.mark.xfail(
    strict=True,
    reason="SELECT con alias de tabla aún pierde columnas en el plan lógico (zona de Andres)",
)
def test_anillo_a_consultas_por_marca_no_dejan_operadores_pendientes(tmp_path):
    resultado = migrar(
        CASO / "programa.sas",
        tmp_path / "salida",
        tablas_locales=REPO / "env/tablas_locales.json",
    )

    lineas_consultas = {32, 48, 64, 90}
    pendientes = [
        pendiente
        for pendiente in resultado.pendientes
        if pendiente.codigo == "P-OPERADOR-SIN-SOPORTE"
        and pendiente.linea in lineas_consultas
    ]
    assert pendientes == []


def test_anillo_a_deja_pendiente_el_borrado_de_tablas_de_sas_studio():
    texto = (CASO / "programa.sas").read_text(encoding="utf-8")
    analisis = analyze_program({"programa.sas": texto})
    plan = compile_file(analisis, "programa.sas", project_base()).plan

    evidencias = [
        evidencia.line_start
        for hueco in plan.gaps
        if hueco.reason == "MACRO_NO_EXPANDIDA"
        for evidencia in hueco.evidence
    ]
    assert sorted(evidencias) == [28, 44, 60, 86]


def test_expansion_estatica_deja_quince_append_sobre_si_mismo_pendientes():
    texto = (CASO / "programa.sas").read_text(encoding="utf-8")
    analisis = analyze_program({"programa.sas": texto})
    plan = compile_file(analisis, "programa.sas", project_base()).plan

    pendientes = [
        operador
        for operador in plan.graph.operators()
        if operador.params.get("pending_code") == "P-APPEND-MISMA-TABLA"
    ]
    assert len(pendientes) == 15
    assert not any(operador.kind == "union" for operador in plan.graph.operators())


def test_anillo_b_sin_repeticiones_conserva_las_filas_base(tmp_path):
    caso = _caso_sin_macros_de_interfaz(tmp_path)

    salidas = calcular(caso, {"repeticiones": 0})

    assert {nombre: len(tabla.filas) for nombre, tabla in salidas.items()} == {
        "ACURA": MARCAS["Acura"],
        "JAGUAR": MARCAS["Jaguar"],
        "BMW": MARCAS["BMW"],
        "CHEVROLET": MARCAS["Chevrolet"],
    }


@pytest.mark.xfail(
    strict=True,
    reason="PROC APPEND sobre la misma tabla aún no duplica filas (Plan B, B-8)",
)
def test_anillo_b_duplica_consultas_por_marca_con_tres_repeticiones(tmp_path):
    caso = _caso_sin_macros_de_interfaz(tmp_path)

    salidas = calcular(caso, {"repeticiones": 3})

    assert {nombre: len(tabla.filas) for nombre, tabla in salidas.items()} == {
        "ACURA": MARCAS["Acura"] * 2**3,
        "JAGUAR": MARCAS["Jaguar"] * 2**3,
        "BMW": MARCAS["BMW"] * 2**3,
        "CHEVROLET": MARCAS["Chevrolet"] * 2**3,
    }
    acura = salidas["ACURA"]
    indice_marca = next(i for i, nombre in enumerate(acura.columnas) if nombre.lower() == "make")
    assert {fila[indice_marca] for fila in acura.filas} == {"Acura"}


def _caso_sin_macros_de_interfaz(tmp_path):
    """Aísla el ciclo de datos: el plan deja las macros web pendientes explícitamente."""
    caso = cargar_caso(CASO)
    texto = caso.programa.read_text(encoding="utf-8")
    texto = re.sub(
        r"(?im)^[ \t]*%web_(?:drop_table|open_table)\([^\r\n)]*\);?[ \t]*$",
        "",
        texto,
    )
    programa = tmp_path / "programa.sas"
    programa.write_text(texto, encoding="utf-8")
    return SimpleNamespace(programa=programa, salidas=caso.salidas, entradas=caso.entradas)
