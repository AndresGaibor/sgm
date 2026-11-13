"""Versiones de salida vacías y validación completa de un lote antes de escribir."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.csv_tabla import Tabla  # noqa: E402
from corpus_lib.esperado_interprete import calcular, escribir  # noqa: E402


@pytest.fixture
def empty_case(tmp_path):
    directory = tmp_path / "L8" / "c1"
    (directory / "entradas").mkdir(parents=True)
    (directory / "entradas" / "e.csv").write_bytes(b"x,y\n")
    (directory / "programa.sas").write_text(
        "proc sql; create table WORK.s as select x from WORK.e; quit;\n"
        "proc sql; create table WORK.s as select y from WORK.e; quit;\n",
        encoding="utf-8",
    )
    (directory / "caso.yaml").write_text(
        yaml.safe_dump({
            "nivel": "L8", "construcciones": ["PROC SQL"], "capa": "B",
            "estado": "parcial", "motivo": "esperado calculado sin SAS real",
            "salidas": ["s"],
        }),
        encoding="utf-8",
    )
    return cargar_caso(directory)


def test_salida_vacia_reemplazada_conserva_cabecera_de_la_ultima_version(empty_case):
    table = calcular(empty_case)["s"]

    assert table.columnas == ["y"]
    assert table.filas == []


def test_lote_con_salida_no_declarada_no_escribe_ninguna_tabla(empty_case):
    tables = {"s": Tabla(["x"], [(1,)]), "no_declarada": Tabla(["x"], [(2,)])}
    assert not empty_case.esperado.exists()

    with pytest.raises(ValueError, match="no_declarada"):
        escribir(empty_case, tables)

    assert not empty_case.esperado.exists()
    assert not list(empty_case.directorio.rglob("s.csv"))
