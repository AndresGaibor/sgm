import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.cli import app
from sgm.ir.models import Column
from sgm.migrar.esquemas_programa import a_json, esquemas_desde_programa, tablas_base_del_programa
from tools.contenedores.fuentes_sas import tablas_base

ROOT = Path(__file__).resolve().parents[2]
SMALL = ROOT / "tests/fixtures/sas/client/client_poc.sas"
LARGE = ROOT / "tests/fixtures/sas/client/client_large.sas"
COLUMNS = [
    "Make",
    "Model",
    "Type",
    "Origin",
    "DriveTrain",
    "MSRP",
    "Invoice",
    "EngineSize",
    "Cylinders",
    "Horsepower",
    "MPG_City",
    "MPG_Highway",
    "Weight",
    "Wheelbase",
    "Length",
]


def test_copia_simple_atribuye_columnas_y_compatibilidad():
    text = SMALL.read_text(encoding="utf-8")
    assert tablas_base_del_programa(text)["sashelp.cars"] == COLUMNS
    assert "sashelp.cars" not in tablas_base_del_programa(text, atribuir_copias=False)
    assert not any(t.biblioteca == "sashelp" and t.tabla == "cars" for t in tablas_base(SMALL)[0])


@pytest.mark.parametrize("operation", ["keep a;", "drop a;", "rename a=b;", "b=a+1;"])
def test_copia_transformada_no_atribuye(operation):
    text = f"data work.c; set lib.t; {operation} run; proc sql; select c.a from work.c c; quit;"
    assert not tablas_base_del_programa(text).get("lib.t")
    _, pending = esquemas_desde_programa(text)
    assert any(
        p.codigo == "P-COLUMNAS-NO-ATRIBUIDAS" and "lib.t" in p.mensaje.lower() for p in pending
    )


def test_tipo_desconocido_y_fixture_solo_para_columnas_declaradas():
    text = SMALL.read_text(encoding="utf-8")
    schemas, pending = esquemas_desde_programa(text)
    assert len(schemas["sashelp.cars"]) == 15
    assert all(c.type == "String" for c in schemas["sashelp.cars"])
    assert any(p.codigo == "P-TIPO-DESCONOCIDO" and "sashelp.cars" in p.mensaje for p in pending)
    schemas, pending = esquemas_desde_programa(
        text, fixtures={"sashelp.cars": [Column("MSRP", "Double", 8, "fixture")]}
    )
    columns = {c.name.lower(): c for c in schemas["sashelp.cars"]}
    assert (columns["msrp"].type, columns["msrp"].source, columns["msrp"].length) == (
        "Double",
        "fixture",
        8,
    )
    assert columns["make"].type == "String"
    assert any(p.codigo == "P-TIPO-DESCONOCIDO" for p in pending)


def test_aritmetica_import_demuestra_tipo():
    text = "proc import datafile='x.csv' out=work.t dbms=dlm replace; getnames=yes; run; data work.u; set work.t; y=a*2; run;"
    schemas, _ = esquemas_desde_programa(text)
    assert next(c for c in schemas["work.t"] if c.name.lower() == "a").type == "Double"


def test_tabla_dinamica_se_reporta():
    _, pending = esquemas_desde_programa("proc sql; select a from &lib..t; quit;")
    assert any(p.codigo == "P-TABLA-DINAMICA" and "&lib..t" in p.mensaje for p in pending)


def test_json_marca_propuesta_y_desconocido_nulo():
    result = a_json({"lib.t": [Column("a", "String", None, "unknown")]}, "p.sas")
    assert result["lib"]["_inferido"] is True
    assert result["lib"]["tables"]["t"][0]["type"] is None


def test_cli_escribe_propuesta_sin_inventar_tipos(tmp_path):
    result = CliRunner().invoke(
        app, ["esquemas", "--desde-programa", str(SMALL), "--salida", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / "sashelp.json").read_text(encoding="utf-8"))
    assert data["_inferido"] and "inferido" in data["source"]
    assert all(c["type"] is None for c in data["tables"]["cars"])


def test_cli_carga_tipos_de_ficha(tmp_path):
    fixtures = ROOT / "tests/fixtures/datos/sashelp"
    result = CliRunner().invoke(
        app,
        [
            "esquemas",
            "--desde-programa",
            str(SMALL),
            "--fixtures",
            str(fixtures),
            "--salida",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / "sashelp.json").read_text(encoding="utf-8"))
    cols = {c["name"].lower(): c for c in data["tables"]["cars"]}
    assert (
        data["_inferido"]
        and cols["msrp"]["type"] == "Double"
        and cols["msrp"]["source"] == "fixture"
    )
    assert cols["make"]["type"] == "String" and cols["make"]["source"] == "fixture"


def test_compatibilidad_programa_grande():
    result = tablas_base(LARGE)
    assert (
        hashlib.sha256(repr(result).encode()).hexdigest()
        == "682e40aab8f1328139666bd6c23e310c0235c6072b35abc67c963c2dcef7b6da"
    )


def test_input_sin_tipo_explicito_no_se_declara_demostrado():
    text = "data work.t; infile 'x'; input a b $; run;"
    schemas, _ = esquemas_desde_programa(text)
    data = a_json(schemas, "p")
    columns = {c["name"].lower(): c for c in data["work"]["tables"]["t"]}
    assert columns["a"]["type"] is None
    assert columns["b"]["type"] is None


def test_no_escribir_en_catalogo_entorno(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["esquemas", "--desde-programa", str(SMALL), "--salida", "env/schemas"]
    )
    assert result.exit_code == 2
    assert not (tmp_path / "env/schemas/sashelp.json").exists()


def test_aritmetica_demuestra_tipo_de_columna_base():
    text = "proc sql; select t.a*2 as z, t.b from lib.t t; quit;"
    schemas, _ = esquemas_desde_programa(text)
    columns = {c.name.lower(): c for c in schemas["lib.t"]}
    assert columns["a"].type == "Double"
    assert columns["b"].source == "unknown"


def test_cargador_no_convierte_propuesta_inferida_en_catalogo(tmp_path):
    from sgm.catalog.schemas import load_schemas

    proposal = {
        "schema": "lib",
        "_inferido": True,
        "source": "inferido del programa p",
        "tables": {"t": [{"name": "a", "type": "Double", "source": "fixture"}]},
    }
    (tmp_path / "lib.json").write_text(json.dumps(proposal), encoding="utf-8")
    assert load_schemas(tmp_path) == {}
