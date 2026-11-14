"""Caso sintético de SQL a Impala de la rebanada K-7b."""

from __future__ import annotations

import csv
import re
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from rebanar_programa import armar, leer_rebanada, verificar  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.seguridad.escaner_secretos import escanear_ruta  # noqa: E402
from tools.contenedores.preparar_rebanada import preparar, sql_de_carga  # noqa: E402
from tools.corpus_lib.caso import cargar_caso  # noqa: E402
from tools.datos_sinteticos.requisitos import requisitos_de_rebanada  # noqa: E402

CASE = REPO / "tests/corpus_reales/L8/k7b_sql_impala"
SOURCE = REPO / "tests/fixtures/sas/client/client_large.sas"
MAP = REPO / "decisiones/client_large.rebanadas.yaml"
BASE_TABLE = "resultados_vspc_clientes.master_customer_data"
BASE_COLUMNS = {
    "cod_tipo_doc",
    "num_doc",
    "nombre_cli",
    "long_nombre1",
    "long_nombre2",
    "long_apellido1",
    "long_apellido2",
    "dir_p",
    "cod_ciudad_dirp",
    "cod_pais_dirp",
    "year",
    "month",
    "ingestion_day",
    "llave_sistema",
    "cod_tipo_dirp",
}


def _case() -> Path:
    assert CASE.is_dir(), "falta el caso K-7b"
    return CASE


def _copy_case(tmp_path: Path) -> Path:
    level = tmp_path / "L8"
    level.mkdir(parents=True, exist_ok=True)
    return shutil.copytree(_case(), level / "k7b_sql_impala")


def test_rebanada_k7b_verifica_hash_y_conserva_el_texto_original():
    case = _case()
    slice_ = leer_rebanada(case / "rebanada.yaml")
    with SOURCE.open(encoding="utf-8", newline="") as source:
        source_text = source.read()

    assert slice_.rangos == ((166, 181), (183, 212))
    assert verificar(slice_, REPO) == []
    assert (case / "programa.sas").read_bytes() == armar(slice_, source_text).encode("utf-8")


def test_requisitos_k7b_incluyen_tablas_y_macros_de_passthrough():
    text = _case().joinpath("programa.sas").read_text(encoding="utf-8")

    requirements = requisitos_de_rebanada(text, "k7b_sql_impala")

    assert set(requirements.tablas_work_externas) == {"work.validacion_fecha"}
    assert {column.casefold() for column in requirements.tablas_work_externas[
        "work.validacion_fecha"
    ]} == {"año", "mes", "dia"}
    assert set(requirements.tablas_base) == {BASE_TABLE}
    assert {column.casefold() for column in requirements.tablas_base[BASE_TABLE]} == BASE_COLUMNS
    assert set(requirements.dinamicos) == {
        f"{BASE_TABLE}.year = &ANIO",
        f"{BASE_TABLE}.month = &MES",
        f"{BASE_TABLE}.ingestion_day = &MDAY",
    }


def test_preparar_y_sqlite_reproducen_maxdia_sin_conectar_a_impala(tmp_path):
    case_dir = _copy_case(tmp_path)
    preparar(case_dir)
    case = cargar_caso(case_dir)
    input_path = case_dir / f"entradas/{BASE_TABLE}.csv"
    with input_path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 12
    assert Counter(row["MONTH"] for row in rows) == {"9": 9, "8": 3}
    september_days = [row["ingestion_day"] for row in rows if row["MONTH"] == "9"]
    assert len(set(september_days)) == 3
    assert Counter(september_days)["2026-09-28"] == 4
    second_dir = _copy_case(tmp_path / "segunda")
    preparar(second_dir)
    assert {
        path.name: path.read_bytes() for path in (case_dir / "entradas").iterdir()
    } == {path.name: path.read_bytes() for path in (second_dir / "entradas").iterdir()}

    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            'CREATE TABLE master_customer_data ("YEAR" TEXT, "MONTH" TEXT, ingestion_day TEXT)'
        )
        connection.executemany(
            "INSERT INTO master_customer_data VALUES (?, ?, ?)",
            [(row["YEAR"], row["MONTH"], row["ingestion_day"]) for row in rows],
        )
        maximum = connection.execute(
            'SELECT MAX(ingestion_day) FROM master_customer_data WHERE "YEAR"=? AND "MONTH"=?',
            ("2026", "9"),
        ).fetchone()[0]

    assert maximum == "2026-09-28"
    assert case.salidas == ("MAXDIA",)
    with (case_dir / "esperado/MAXDIA.csv").open(encoding="utf-8", newline="") as expected:
        assert list(csv.reader(expected)) == [["Mday"], [maximum]]


def test_sql_de_carga_no_inventa_tipo_numerico_para_anio_ni_mes():
    sql = sql_de_carga(_case()).casefold()

    assert "resultados_vspc_clientes.master_customer_data" in sql
    assert re.search(r"`year`\s+string", sql)
    assert re.search(r"`month`\s+string", sql)


def test_migrar_k7b_usa_contexto_dev_y_genera_timpala_sin_conectar(tmp_path):
    case = _case()
    result = migrar(
        case / "programa.sas",
        tmp_path / "out",
        contexto_dev=REPO / "env/contexto_dev.json",
    )
    assert result.jobs
    assert any(
        node.componente == "tImpalaRow"
        for job in result.jobs
        for node in job.nodos
    )
    dev_context = (result.carpeta / "contextos/DEV.yaml").read_text(encoding="utf-8")
    assert 'valor: "localhost"' in dev_context
    item_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.carpeta.rglob("*.item")
    )
    assert "context.impala_host" in item_text
    pending_codes = {item.codigo for item in result.pendientes}
    assert "P-OPERADOR-SIN-SOPORTE" in pending_codes
    assert "P-CONEXION-BASE" in pending_codes
    assert "P-FALLO-INTERNO" not in pending_codes


def test_k7b_caso_y_job_no_exponen_secretos(tmp_path):
    case = _case()
    result = migrar(
        case / "programa.sas",
        tmp_path / "out",
        contexto_dev=REPO / "env/contexto_dev.json",
    )

    assert escanear_ruta(case).hallazgos == ()
    assert escanear_ruta(result.carpeta).hallazgos == ()
