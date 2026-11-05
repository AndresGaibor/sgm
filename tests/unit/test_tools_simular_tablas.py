"""Pruebas de `tools/simular_tablas.py`: emulación de las tablas Impala con CSV."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
SCRIPT = REPO / "tools" / "simular_tablas.py"


def _ejecutar(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURE), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_escribe_un_csv_por_tabla_impala_del_programa(tmp_path):
    resultado = _ejecutar(str(tmp_path), "--filas", "3")

    assert resultado.returncode == 0, resultado.stderr
    nombres = {archivo.name for archivo in tmp_path.glob("*.csv")}
    assert "resultados_vspc_clientes.master_customer_data.csv" in nombres
    assert "S_CANALES.SAI_SCILIBRAMD_SCIFFIMGFR.csv" in nombres
    # Solo tablas con biblioteca: los datasets de SAS y los marcadores de macro no se simulan.
    assert all("." in nombre for nombre in nombres)


def test_las_columnas_salen_del_sql_y_las_filas_son_simuladas(tmp_path):
    _ejecutar(str(tmp_path), "--filas", "2")

    maestro = (tmp_path / "resultados_vspc_clientes.master_customer_data.csv").read_text(
        encoding="utf-8"
    )
    lineas = maestro.splitlines()
    assert {"ingestion_day", "YEAR", "MONTH"} <= set(lineas[0].split(";"))
    assert len(lineas) == 3
    assert all(valor.startswith("SIM_") for valor in lineas[1].split(";"))

    firmas = (tmp_path / "S_CANALES.SAI_SCILIBRAMD_SCIFFIMGFR.csv").read_text(
        encoding="utf-8"
    )
    assert firmas.splitlines()[0].split(";") == [
        "ingestion_day",
        "ingestion_month",
        "ingestion_year",
    ]


def test_deja_la_convencion_de_simulacion(tmp_path):
    _ejecutar(str(tmp_path), "--filas", "1")

    convencion = (tmp_path / "CONVENCION.md").read_text(encoding="utf-8")
    assert "modo_simulacion" in convencion
    assert "tFileInputDelimited" in convencion
    assert "tImpalaInput" in convencion


def test_un_programa_sin_impala_no_escribe_csv(tmp_path):
    programa = tmp_path / "sin_impala.sas"
    programa.write_text(
        "proc sql;\ncreate table x as select 1 from work.y;\nquit;\n", encoding="utf-8"
    )

    resultado = subprocess.run(
        [sys.executable, str(SCRIPT), str(programa), str(tmp_path / "datos")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert list((tmp_path / "datos").glob("*.csv")) == []
