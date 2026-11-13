"""Generación determinista y SQL tipado a partir de esquemas explícitos."""

import argparse
import json
from pathlib import Path

import pytest

from sgm.catalog.schemas import load_schemas
from sgm.ir.models import Column
from tools.contenedores.cargar_tablas import construir_sql
from tools.contenedores.sql_carga import sentencias_tipadas, sql_conteos
from tools.datos_sinteticos.por_esquema import generar_filas

COLS = [
    Column("id", "Integer"),
    Column("nombre", "String"),
    Column("saldo", "Double"),
    Column("f", "Date"),
]


def test_generador_tipos_y_aviso():
    header, rows, warnings = generar_filas("b.t", COLS, 3)
    assert header == ["id", "nombre", "saldo", "f"] and len(rows) == 3
    assert all(1 <= int(row[0]) <= 1000 for row in rows)
    assert [row[1] for row in rows] == ["SIM_nombre-001", "SIM_nombre-002", "SIM_nombre-003"]
    assert all(len(row[2].split(".")[1]) == 2 for row in rows)
    assert any("P-TIPO-GENERADOR" in w and "f" in w and "Date" in w for w in warnings)


def test_semilla_determinista_y_cambio_de_valores():
    first = generar_filas("b.t", COLS, 5, semilla=7)
    assert first == generar_filas("b.t", COLS, 5, semilla=7)
    second = generar_filas("b.t", COLS, 5, semilla=8)
    assert [r[0] for r in first[1]] != [r[0] for r in second[1]]
    assert [r[2] for r in first[1]] != [r[2] for r in second[1]]


def test_valores_exigidos_y_limite_de_filas():
    _, rows, _ = generar_filas("b.t", COLS, 3, exigidos={"nombre": ["Acura", "BMW"]})
    assert [r[1] for r in rows[:2]] == ["Acura", "BMW"]
    with pytest.raises(ValueError):
        generar_filas("b.t", COLS, 1, exigidos={"nombre": ["Acura", "BMW"]})


def test_tipo_ausente_no_genera_aviso():
    _, rows, warnings = generar_filas("b.t", [Column("x", None)], 1)
    assert rows == [["SIM_x-001"]] and warnings == []


def test_sql_tipado_exacto_y_conteos():
    assert sentencias_tipadas("b", "t", COLS[:3], [["1", "SIM_nombre-001", "10.50"]]) == [
        "CREATE DATABASE IF NOT EXISTS b;",
        "DROP TABLE IF EXISTS b.t;",
        "CREATE TABLE b.t (\n  `id` INT,\n  `nombre` STRING,\n  `saldo` DOUBLE\n);",
        "INSERT INTO b.t VALUES\n  (1, 'SIM_nombre-001', 10.50);",
    ]
    sql = sql_conteos([("b", "t"), ("b", "u")]).lower()
    assert sql.count("union all") == 1 and "from b.u" in sql


@pytest.mark.parametrize("value", ["1); DROP TABLE b.t;--", "nan", "Infinity", "1e9999"])
def test_sql_rechaza_numericos_no_seguros(value):
    with pytest.raises(ValueError):
        sentencias_tipadas("b", "t", [Column("x", "Double")], [[value]])


def test_sql_escapa_texto_y_rechaza_identificadores_inseguros():
    sql = "\n".join(sentencias_tipadas("b", "t", [Column("x", "String")], [["O'Brien"]]))
    assert "'O''Brien'" in sql
    with pytest.raises(ValueError):
        sentencias_tipadas("b; DROP DATABASE x", "t", [Column("x", "String")], [["v"]])


def test_propuesta_inferida_alimenta_sql_sin_entrar_en_catalogo(tmp_path):
    source = tmp_path / "p.sas"
    source.write_text(
        "proc sql; select t.id, t.saldo from lib.t t; select u.a from lib.u u; quit;",
        encoding="utf-8",
    )
    schemas = tmp_path / "esquemas"
    schemas.mkdir()
    proposal = {
        "schema": "lib",
        "source": "inferido del programa p",
        "_inferido": True,
        "tables": {
            "t": [
                {"name": "id", "type": "Integer", "source": "derived"},
                {"name": "saldo", "type": "Double", "source": "fixture"},
            ]
        },
    }
    (schemas / "lib.json").write_text(json.dumps(proposal), encoding="utf-8")
    assert load_schemas(schemas) == {}
    args = argparse.Namespace(
        sas=str(source), csv=None, tabla=None, filas=3, esquemas=str(schemas), semilla=20261104
    )
    sql, warnings = construir_sql(args)
    assert "`id` INT" in sql and "`saldo` DOUBLE" in sql
    assert "`a` STRING" in sql and not any("lib.t" in w for w in warnings)


def test_script_directo_funciona_fuera_de_raiz(tmp_path):
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[2] / "tools/contenedores/cargar_tablas.py"
    source = tmp_path / "p.sas"
    source.write_text("proc sql; select t.id from lib.t t; quit;", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(script), "--sas", str(source), "--filas", "1"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "CREATE TABLE lib.t" in result.stdout


def test_lector_explicito_conserva_origen_y_desconocido(tmp_path):
    from tools.contenedores.esquemas_datos import cargar_esquemas_datos

    payload = {
        "_inferido": True,
        "source": "inferido de p",
        "tables": {
            "t": [
                {"name": "a", "type": "Double", "source": "fixture"},
                {"name": "b", "type": None, "source": "unknown"},
            ]
        },
    }
    (tmp_path / "lib.json").write_text(json.dumps(payload), encoding="utf-8")
    columns = cargar_esquemas_datos(tmp_path)["lib.t"]
    assert [(c.name, c.type, c.source) for c in columns] == [
        ("a", "Double", "fixture"),
        ("b", None, "unknown"),
    ]
    assert load_schemas(tmp_path) == {}


def test_sql_escapa_barra_inversa_y_comilla():
    result = sentencias_tipadas("b", "t", [Column("x", "String")], [["a\\'b"]])[-1]
    assert "'a\\\\''b'" in result


def test_sin_filas_no_escribe_insert_invalido():
    from tools.contenedores.fuentes_sas import TablaBase
    from tools.contenedores.sql_carga import sentencias_ficticias

    assert not any(
        s.startswith("INSERT") for s in sentencias_ficticias(TablaBase("b", "t", ("a",)), 0)
    )


def test_verificar_sql_se_imprime_sin_ejecutar(tmp_path, capsys):
    from tools.contenedores.cargar_tablas import main

    source = tmp_path / "p.sas"
    source.write_text("proc sql; select t.id from lib.t t; quit;", encoding="utf-8")
    assert main(["--sas", str(source), "--verificar"]) == 0
    assert "count(*) as filas from lib.t" in capsys.readouterr().out.lower()


@pytest.mark.parametrize(("returned", "expected"), [("3", 0), ("2", 1)])
def test_verificacion_compara_conteos_sin_base(tmp_path, monkeypatch, returned, expected, capsys):
    import subprocess

    import tools.contenedores.cargar_tablas as cli

    source = tmp_path / "p.sas"
    source.write_text("proc sql; select t.id from lib.t t; quit;", encoding="utf-8")

    def simular(sql):
        output = f"| lib.t | {returned} |\n" if "count(*)" in sql else ""
        return subprocess.CompletedProcess([], 0, stdout=output, stderr="")

    monkeypatch.setattr(cli, "ejecutar_sql", simular)
    result = cli.main(["--sas", str(source), "--filas", "3", "--ejecutar", "--verificar"])
    assert result == expected
    output = capsys.readouterr()
    assert (
        ("Conteos verificados" in output.out)
        if expected == 0
        else ("Conteo no coincide" in output.err)
    )


def test_rechaza_carpeta_de_esquemas_inexistente(tmp_path):
    source = tmp_path / "p.sas"
    source.write_text("proc sql; select t.id from lib.t t; quit;", encoding="utf-8")
    args = argparse.Namespace(
        sas=str(source), csv=None, tabla=None, filas=1, esquemas=str(tmp_path / "faltan"), semilla=1
    )
    with pytest.raises(ValueError, match="esquemas"):
        construir_sql(args)


def test_csv_no_acepta_identificador_de_columna_peligroso(tmp_path):
    from tools.contenedores.sql_carga import sentencias_desde_csv

    path = tmp_path / "datos.csv"
    path.write_text("mal`nombre\nx\n", encoding="utf-8")
    with pytest.raises(ValueError):
        sentencias_desde_csv("b", "t", path)


@pytest.mark.parametrize(
    ("name", "value"), [("id", "3; DROP TABLE b.t"), ("saldo", "nan"), ("id", "2147483648")]
)
def test_generador_rechaza_valor_exigido_incompatible(name, value):
    with pytest.raises(ValueError):
        generar_filas("b.t", COLS, 1, exigidos={name: [value]})


def test_rechaza_esquema_vacio_o_columnas_ambiguas():
    with pytest.raises(ValueError):
        sentencias_tipadas("b", "t", [], [])
    duplicates = [Column("x", "String"), Column("X", "String")]
    with pytest.raises(ValueError):
        sentencias_tipadas("b", "t", duplicates, [["a", "b"]])
    with pytest.raises(ValueError):
        generar_filas("b.t", duplicates, 1)
