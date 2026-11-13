"""Regresiones de tablas de entrada y SQL para el hito 229n."""

import argparse
import json
import subprocess

import pytest

from sgm.catalog.schemas import load_schemas
from sgm.ir.models import Column
from tools.contenedores.cargar_tablas import construir_sql, main
from tools.contenedores.esquemas_datos import cargar_esquemas_datos
from tools.contenedores.fuentes_sas import TablaBase
from tools.contenedores.sql_carga import (
    sentencias_desde_csv,
    sentencias_ficticias,
    sentencias_tipadas,
    sql_conteos,
)


def test_esquemas_atribuye_lectura_de_copia_simple(tmp_path):
    source = tmp_path / "p.sas"
    source.write_text(
        "data work.c; set lib.t; run; proc sql; select c.x from work.c c; quit;", encoding="utf-8"
    )
    folder = tmp_path / "schemas"
    folder.mkdir()
    (folder / "lib.json").write_text(
        json.dumps(
            {
                "_inferido": True,
                "tables": {"t": [{"name": "x", "type": "Double", "source": "derived"}]},
            }
        ),
        encoding="utf-8",
    )
    sql, avisos = construir_sql(
        argparse.Namespace(
            sas=str(source), csv=None, tabla=None, filas=2, esquemas=str(folder), semilla=1
        )
    )
    assert "`x` DOUBLE" in sql and "INSERT INTO lib.t" in sql
    assert not any("lib.t" in a and "OMITIDA" in a for a in avisos)


@pytest.mark.parametrize("mixed", [False, True])
def test_verifica_conteo_real_csv_y_filas_sinteticas(tmp_path, monkeypatch, mixed):
    import tools.contenedores.cargar_tablas as cli

    csv = tmp_path / "datos.csv"
    csv.write_text("id\n1\n2\n", encoding="utf-8")
    args = [
        "--csv",
        str(csv),
        "--tabla",
        "lib.csvtabla",
        "--filas",
        "3",
        "--ejecutar",
        "--verificar",
    ]
    if mixed:
        source = tmp_path / "p.sas"
        source.write_text("proc sql; select t.x from lib.t t; quit;", encoding="utf-8")
        args += ["--sas", str(source)]

    def fake(sql):
        stdout = (
            "| lib.csvtabla | 2 |\n" + ("| lib.t | 3 |\n" if mixed else "")
            if "count(*)" in sql
            else ""
        )
        return subprocess.CompletedProcess([], 0, stdout=stdout, stderr="")

    monkeypatch.setattr(cli, "ejecutar_sql", fake)
    assert main(args) == 0


def test_identificadores_reservados_citados_en_todas_las_sentencias(tmp_path):
    path = tmp_path / "datos.csv"
    path.write_text("id\n1\n", encoding="utf-8")
    statements = [
        *sentencias_tipadas("select", "table", [Column("id", "Integer")], [["1"]]),
        *sentencias_ficticias(TablaBase("select", "table", ("id",)), 1),
        *sentencias_desde_csv("select", "table", path),
        sql_conteos([("select", "table")]),
    ]
    for statement in statements:
        if statement.startswith("CREATE DATABASE"):
            assert "`select`" in statement
        else:
            assert "`select`.`table`" in statement


def test_catalogo_explicito_tiene_prioridad_sobre_propuesta(tmp_path, monkeypatch):
    import tools.contenedores.esquemas_datos as module

    official = tmp_path / "oficial"
    proposal = tmp_path / "propuesta"
    official.mkdir()
    proposal.mkdir()
    (official / "lib.json").write_text(
        json.dumps({"tables": {"t": [{"name": "x", "type": "Integer"}]}}), encoding="utf-8"
    )
    (proposal / "lib.json").write_text(
        json.dumps(
            {
                "_inferido": True,
                "tables": {"t": [{"name": "x", "type": "Double", "source": "derived"}]},
            }
        ),
        encoding="utf-8",
    )
    official_data = load_schemas(official)
    monkeypatch.setattr(module, "load_schemas", lambda folder: official_data)
    result = cargar_esquemas_datos(proposal)
    assert (result["lib.t"][0].type, result["lib.t"][0].source) == ("Integer", "catalog")


@pytest.mark.parametrize("nombre", ["timestamp", "string"])
def test_tipos_reservados_se_citan_como_nombres_de_tabla(nombre):
    sql = sentencias_tipadas("lib", nombre, [Column("x", "Integer")], [["1"]])
    assert all(f"`{nombre}`" in s for s in sql[1:])
