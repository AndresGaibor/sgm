"""Pruebas del catálogo documental de SAS (`rules/sas/catalogo/`).

Tres cosas: cada página citada existe en el índice de la guía; el validador acepta los archivos y
rechaza una entrada sin página; y lo que el catálogo dice que está "reconocida" o "no_reconocida"
coincide con lo que hace el parser de hoy.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from sgm import rules_validate
from sgm.frontend.datastep import classify_statement
from sgm.frontend.sql import parse_sql_statement

REPO = Path(__file__).resolve().parents[2]
CATALOGO = REPO / "rules" / "sas" / "catalogo"
REF = REPO / "docs" / "referencia" / "sas"

# Guía de cada catálogo: el índice que debe contener cada página citada.
GUIA_DE_CITA = {
    "lefunctionsref.pdf": "lefunctionsref.INDEX.md",
    "lestmtsref.pdf": "lestmtsref.INDEX.md",
    "sqlproc.pdf": "sqlproc.INDEX.md",
    "mcrolref.pdf": "mcrolref.INDEX.md",
    "ledsoptsref.pdf": "ledsoptsref.INDEX.md",
}


def _catalogos() -> dict[str, dict]:
    return {
        p.stem: yaml.safe_load(p.read_text(encoding="utf-8"))
        for p in sorted(CATALOGO.glob("*.yaml"))
    }


def _entradas(nombre: str) -> list[dict]:
    return _catalogos()[nombre]["entries"]


def test_el_validador_acepta_el_catalogo():
    problemas = [p for p in rules_validate.validate() if p.file.startswith("rules/sas/catalogo/")]
    assert problemas == []


def test_una_entrada_sin_pagina_no_pasa_el_esquema():
    datos = {
        "id": "x",
        "kind": "catalogo",
        "version": 1,
        "description": "prueba",
        "entries": [{"id": "a", "nombre": "A", "fuente": "lestmtsref.pdf", "estado": "reconocida"}],
    }
    problemas = rules_validate._check_schema(
        "x.yaml", datos, "", rules_validate._schema("catalogo", rules_validate.ROOT)
    )
    assert problemas, "una fuente sin 'p. N' debe fallar la validación"


@pytest.mark.parametrize("nombre", sorted(_catalogos()))
def test_cada_pagina_citada_existe_en_el_indice_de_su_guia(nombre):
    for entrada in _entradas(nombre):
        guia, pagina = re.fullmatch(r"(.+?), p\. (\d+)", entrada["fuente"]).groups()
        indice = (REF / GUIA_DE_CITA[guia]).read_text(encoding="utf-8")
        assert f"(p. {pagina})" in indice, f"{nombre}: {entrada['nombre']} cita p. {pagina}"


def test_cada_regla_de_funcion_citada_existe():
    for entrada in _entradas("funciones-usadas"):
        if entrada["estado"] == "reconocida":
            ruta = re.search(r"rules/sas/functions/\S+\.yaml", entrada["nota"]).group(0)
            assert (REPO / ruta).exists(), ruta


# Una muestra por palabra clave que el parser del DATA step reconoce.
MUESTRAS_DATA_STEP = {
    "SET": "set a;",
    "MERGE": "merge a b;",
    "BY": "by x;",
    "WHERE": "where x=1;",
    "OUTPUT": "output a;",
    "KEEP": "keep x;",
    "DROP": "drop x;",
    "RENAME": "rename a=b;",
    "RETAIN": "retain x;",
    "FORMAT": "format x best.;",
    "INFORMAT": "informat x best.;",
    "LENGTH": "length x 8;",
    "LABEL": "label x='a';",
    "ATTRIB": "attrib x length=8;",
    "ARRAY": "array a x y;",
    "DO": "do i=1 to 3;",
    "END": "end;",
    "INFILE": "infile 'a';",
    "INPUT": "input x;",
}


def test_las_sentencias_reconocidas_las_clasifica_el_parser():
    reconocidas = {
        e["nombre"].replace(" Statement", "").upper()
        for e in _entradas("sentencias-data-step")
        if e["estado"] == "reconocida"
    }
    for palabra, muestra in MUESTRAS_DATA_STEP.items():
        assert palabra in reconocidas, f"{palabra} debería figurar como reconocida"
        assert classify_statement(muestra, 1).kind != "other", muestra


def test_las_sentencias_no_reconocidas_quedan_como_other():
    for entrada in _entradas("sentencias-data-step"):
        if entrada["estado"] != "no_reconocida":
            continue
        palabra = entrada["nombre"].replace(" Statement", "").strip()
        if palabra.startswith("%") or palabra.endswith(":"):
            continue  # formas de macro y etiquetas: fuera de esta muestra
        muestra = f"{palabra.lower()} x;"
        assert classify_statement(muestra, 1).kind == "other", muestra


@pytest.mark.parametrize(
    "sentencia, tipo",
    [
        ("create table x as select a from y", "create_table"),
        ("insert into x values (1)", "insert"),
        ("delete from x", "delete"),
        ("drop table x", "drop_table"),
        ("connect to oracle", "connect"),
        ("disconnect from oracle", "disconnect"),
    ],
)
def test_sentencias_proc_sql_reconocidas(sentencia, tipo):
    assert parse_sql_statement(sentencia, 1).kind == tipo


@pytest.mark.parametrize(
    "sentencia",
    [
        "alter table x add a int",
        "create index i on x(a)",
        "create view v as select a from x",
        "describe table x",
        "reset noprint",
        "update x set a=1",
    ],
)
def test_sentencias_proc_sql_no_reconocidas_quedan_como_other(sentencia):
    assert parse_sql_statement(sentencia, 1).kind == "other"


def test_having_y_union_quedan_dentro_del_select_con_sus_tablas():
    having = parse_sql_statement("select a from x group by a having count(*) > 1", 1)
    assert having.kind == "select" and having.sources == ("x",)
    union = parse_sql_statement("select a from x union select a from y", 1)
    assert union.kind == "select" and set(union.sources) == {"x", "y"}


def test_la_opcion_in_se_lee_como_indicadora():
    st = classify_statement("set a(in=b);", 1)
    assert st.fields["sources"][0]["in"] == "b"
    estados = {e["nombre"]: e["estado"] for e in _entradas("opciones-dataset")}
    assert estados["IN="] == "reconocida"


def test_los_nulos_de_sql_no_tienen_regla_implementada():
    for entrada in _entradas("sql-nulos"):
        assert entrada["estado"] == "no_verificada"


def test_las_funciones_de_las_reglas_existen_en_la_guia():
    indice = (REF / "lefunctionsref.INDEX.md").read_text(encoding="utf-8").upper()
    for regla in sorted((REPO / "rules" / "sas" / "functions").glob("fn-*.yaml")):
        nombre = yaml.safe_load(regla.read_text(encoding="utf-8"))["sas"].upper()
        assert f"{nombre} FUNCTION" in indice, f"{regla.name}: {nombre} no está en la guía"
