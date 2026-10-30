"""`sgm env import-describe` (F1.9): la salida de DESCRIBE de Impala se vuelve env/schemas/<esquema>.json."""

import datetime as dt

import pytest
from typer.testing import CliRunner

from sgm.catalog import describe
from sgm.catalog.schemas import load_schemas
from sgm.cli import app

SALIDA = """\
clientes
+------------+-------------+---------+
| name       | type        | comment |
+------------+-------------+---------+
| cliente_id | int         |         |
| nombre     | varchar(60) |         |
| saldo      | decimal(12,2)|        |
| alta       | timestamp   |         |
| activa     | boolean     |         |
| etiquetas  | array<int>  |         |
+------------+-------------+---------+

cuentas
cuenta_id\tbigint\t
tipo\tstring\t
"""


def test_traduce_tipos_de_impala():
    assert describe.traducir("int") == ("Integer", None)
    assert describe.traducir("varchar(60)") == ("String", 60)
    assert describe.traducir("decimal(12,2)") == ("BigDecimal", None)
    assert describe.traducir("bigint") == ("Long", None)
    assert describe.traducir("timestamp") == ("Date", None)
    assert describe.traducir("array<int>") == (None, None)


def test_parsea_varias_tablas_con_tabla_y_tabulador():
    tablas = describe.parsear(SALIDA, "ejemplo_lz")
    assert [c.name for c in tablas["clientes"]][:3] == ["cliente_id", "nombre", "saldo"]
    assert [c.name for c in tablas["cuentas"]] == ["cuenta_id", "tipo"]
    etiquetas = next(c for c in tablas["clientes"] if c.name == "etiquetas")
    assert etiquetas.type is None and etiquetas.impala == "array<int>"


def test_tabla_de_otro_esquema_falla():
    with pytest.raises(ValueError, match="no es del esquema"):
        describe.parsear("otra_lib.clientes\nid\tint\n", "ejemplo_lz")


def test_importar_escribe_el_esquema_que_carga_el_compilador(tmp_path):
    archivo = tmp_path / "describe.txt"
    archivo.write_text(SALIDA, encoding="utf-8")
    ruta, _ = describe.importar(
        archivo, "ejemplo_lz", destino=tmp_path / "schemas", hoy=dt.date(2026, 10, 30)
    )
    assert ruta.name == "ejemplo_lz.json"
    columnas = load_schemas(tmp_path / "schemas")["ejemplo_lz.clientes"]
    tipos = {c.name: c.type for c in columnas}
    assert tipos["cliente_id"] == "Integer" and tipos["saldo"] == "BigDecimal"
    assert tipos["etiquetas"] is None


def test_importar_conserva_las_tablas_que_no_trae_el_archivo(tmp_path):
    destino = tmp_path / "schemas"
    primero = tmp_path / "a.txt"
    primero.write_text("clientes\nid\tint\n", encoding="utf-8")
    segundo = tmp_path / "b.txt"
    segundo.write_text("cuentas\nid\tbigint\n", encoding="utf-8")
    describe.importar(primero, "ejemplo_lz", destino=destino)
    describe.importar(segundo, "ejemplo_lz", destino=destino)
    assert set(load_schemas(destino)) == {"ejemplo_lz.clientes", "ejemplo_lz.cuentas"}


def test_archivo_sin_columnas_falla(tmp_path):
    archivo = tmp_path / "vacio.txt"
    archivo.write_text("solo texto sin columnas\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no encontré columnas"):
        describe.importar(archivo, "ejemplo_lz", destino=tmp_path / "schemas")


def test_nombre_de_esquema_invalido_falla(tmp_path):
    archivo = tmp_path / "x.txt"
    archivo.write_text("clientes\nid\tint\n", encoding="utf-8")
    with pytest.raises(ValueError, match="minúsculas"):
        describe.importar(archivo, "../escape", destino=tmp_path / "schemas")


def test_cli_import_describe(tmp_path, monkeypatch):
    monkeypatch.setattr(describe, "ESQUEMAS", tmp_path / "schemas")
    archivo = tmp_path / "describe.txt"
    archivo.write_text(SALIDA, encoding="utf-8")
    resultado = CliRunner().invoke(
        app, ["env", "import-describe", str(archivo), "--schema", "ejemplo_lz"]
    )
    assert resultado.exit_code == 0, resultado.output
    assert (tmp_path / "schemas" / "ejemplo_lz.json").exists()
    assert "clientes" in resultado.output
