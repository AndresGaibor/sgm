"""Preparación determinista de fixtures y carga opcional por rebanada."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import pytest
import yaml

from tools.contenedores import preparar_rebanada

_PROGRAM_SUM = """proc sql;
create table WORK.t as
select k, sum(v) as s from WORK.z group by k;
quit;
"""
_WORK_MANIFEST = """semilla: 7
tablas:
  work.z:
    filas: 4
    columnas: [k, v]
    fijos:
      k: a
"""


def _create_case(
    directory: Path, program: str = _PROGRAM_SUM, manifest: str = _WORK_MANIFEST
) -> Path:
    directory.mkdir()
    (directory / "programa.sas").write_text(program, encoding="utf-8")
    (directory / "datos.yaml").write_text(manifest, encoding="utf-8")
    return directory


def _input_csv(case: Path) -> Path:
    return next((case / "entradas").glob("*.csv"))


def test_prepare_writes_rows_provenance_and_demonstrated_numeric_type(tmp_path):
    case = _create_case(tmp_path / "case")

    written = preparar_rebanada.preparar(case)

    csv_path = _input_csv(case)
    with csv_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    provenance = yaml.safe_load(csv_path.with_suffix(".ficha.yaml").read_text(encoding="utf-8"))
    assert written == [csv_path]
    assert list(rows[0]) == ["k", "v"]
    assert len(rows) == 4 and {row["k"] for row in rows} == {"a"}
    assert all("." in row["v"] for row in rows)
    assert provenance["origen"] == "sintetico" and provenance["semilla"] == 7
    assert provenance["columnas"] == {"k": "String", "v": "Double"}


def test_prepare_is_reproducible_in_separate_directories(tmp_path):
    first = _create_case(tmp_path / "first")
    second = _create_case(tmp_path / "second")

    preparar_rebanada.preparar(first)
    preparar_rebanada.preparar(second)

    def file_bytes(case):
        return {
            path.relative_to(case / "entradas").as_posix(): path.read_bytes()
            for path in sorted((case / "entradas").iterdir())
        }
    assert file_bytes(first) == file_bytes(second)


def test_load_sql_keeps_unproven_columns_untyped(tmp_path):
    program = """proc sql;
connect to impala (dsn=local);
create table WORK.copia as
select * from connection to impala (select id, amount from proceso.t);
disconnect from impala;
quit;
"""
    manifest = """semilla: 3
tablas:
  proceso.t:
    filas: 2
    columnas: [id, amount]
"""
    case = _create_case(tmp_path / "case", program, manifest)

    sql = preparar_rebanada.sql_de_carga(case)

    assert "CREATE TABLE proceso.t (" in sql
    assert "`id` STRING" in sql and "`amount` STRING" in sql
    assert " DOUBLE" not in sql
    assert not (case / "entradas").exists()


def test_load_sql_uses_double_only_with_numeric_evidence(tmp_path):
    program = """proc sql;
select amount * 2 as calculado from proceso.t;
quit;
"""
    manifest = """semilla: 3
tablas:
  proceso.t:
    filas: 2
    columnas: [id, amount]
"""
    case = _create_case(tmp_path / "case", program, manifest)

    sql = preparar_rebanada.sql_de_carga(case)

    assert "`id` STRING" in sql and "`amount` DOUBLE" in sql


def test_load_reports_the_container_when_it_is_unavailable(tmp_path, monkeypatch):
    case = _create_case(
        tmp_path / "case",
        """proc sql; select id from proceso.t; quit;""",
        """semilla: 3
tablas:
  proceso.t:
    filas: 2
    columnas: [id]
""",
    )

    def unavailable_container(_sql):
        raise RuntimeError("docker: daemon no disponible")

    monkeypatch.setattr(preparar_rebanada, "ejecutar_sql", unavailable_container)
    with pytest.raises(RuntimeError, match="sgmtest_impalad"):
        preparar_rebanada.preparar(case, cargar=True)


def test_load_verifies_row_counts_without_connecting_in_the_test(tmp_path, monkeypatch):
    case = _create_case(
        tmp_path / "case",
        """proc sql; select id from proceso.t; quit;""",
        """semilla: 3
tablas:
  proceso.t:
    filas: 2
    columnas: [id]
""",
    )
    calls = []

    def run_sql(sql):
        calls.append(sql)
        if len(calls) == 1:
            return subprocess.CompletedProcess([], 0, "", "")
        output = "+-----------+-------+\n| tabla     | filas |\n| proceso.t | 2     |\n"
        return subprocess.CompletedProcess([], 0, output, "")

    monkeypatch.setattr(preparar_rebanada, "ejecutar_sql", run_sql)

    preparar_rebanada.preparar(case, cargar=True)

    assert len(calls) == 2
    assert "CREATE TABLE proceso.t" in calls[0]
    assert "count(*)" in calls[1].lower()


def test_load_fails_when_a_row_count_does_not_match(tmp_path, monkeypatch):
    case = _create_case(
        tmp_path / "case",
        """proc sql; select id from proceso.t; quit;""",
        """semilla: 3
tablas:
  proceso.t:
    filas: 2
    columnas: [id]
""",
    )
    responses = iter(
        [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "proceso.t,1\n", ""),
        ]
    )
    monkeypatch.setattr(preparar_rebanada, "ejecutar_sql", lambda _sql: next(responses))

    with pytest.raises(RuntimeError, match="proceso.t.*1.*2"):
        preparar_rebanada.preparar(case, cargar=True)


def test_main_prepares_inputs_from_the_requested_directory(tmp_path, capsys):
    case = _create_case(tmp_path / "case")

    result = preparar_rebanada.main([str(case)])

    assert result == 0
    assert "Entradas preparadas: 1" in capsys.readouterr().out
    assert _input_csv(case).is_file()


def test_load_sql_reports_a_missing_manifest_table_without_key_error(tmp_path):
    case = _create_case(
        tmp_path / "case",
        "proc sql; select id from proceso.t; quit;",
        "semilla: 3\ntablas: {}\n",
    )

    with pytest.raises(ValueError, match="proceso.t: falta en datos.yaml"):
        preparar_rebanada.sql_de_carga(case)
