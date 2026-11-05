"""Pruebas de `tools/simular_productos.py`: archivos delimitados por `;` con 23 columnas y saldo numérico."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
SCRIPT = REPO / "tools" / "simular_productos.py"
COLUMNA_SALDO = "FIN_SALDO_CTA"


def _ejecutar(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURE), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_escribe_archivos_con_23_columnas_y_filas_pedidas(tmp_path):
    resultado = _ejecutar(str(tmp_path), "--filas", "3")

    assert resultado.returncode == 0, resultado.stderr
    archivos = sorted(tmp_path.glob("*.csv"))
    assert archivos, "el simulador no escribió ningún archivo"
    for archivo in archivos:
        lineas = archivo.read_text(encoding="utf-8").splitlines()
        assert len(lineas) == 3
        for linea in lineas:
            assert len(linea.split(";")) == 23


def test_sin_saldo_todas_las_columnas_son_texto(tmp_path):
    _ejecutar(str(tmp_path), "--filas", "2")

    primera = (tmp_path / "DBIFTCD.csv").read_text(encoding="utf-8").splitlines()[0]
    ultima = primera.split(";")[-1]
    assert ultima.startswith("SIM_")
    assert not ultima.replace(".", "").isdigit()


def test_con_saldo_la_ultima_columna_es_numerica(tmp_path):
    resultado = _ejecutar(str(tmp_path), "--filas", "3", "--saldo", COLUMNA_SALDO)

    assert resultado.returncode == 0, resultado.stderr
    lineas = (tmp_path / "DBIFTCD.csv").read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 3
    saldos = [linea.split(";")[-1] for linea in lineas]
    assert saldos == ["100.50", "201.00", "301.50"]
    for linea in lineas:
        assert len(linea.split(";")) == 23
