"""Prueba optativa contra el contenedor local desechable sgmtest_impalad."""

import re
import shutil
import subprocess
from decimal import Decimal
from uuid import uuid4

import pytest

from sgm.ir.models import Column
from tools.contenedores.cargar_tablas import ejecutar_sql
from tools.contenedores.sql_carga import sentencias_tipadas

pytestmark = pytest.mark.contenedores


def test_carga_tipada_y_suma_en_impala():
    if not shutil.which("docker"):
        pytest.skip("Docker no está disponible")
    estado = subprocess.run(
        ["docker", "ps", "--filter", "name=^/sgmtest_impalad$", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if estado.returncode or "sgmtest_impalad" not in estado.stdout.splitlines():
        pytest.skip("contenedor sgmtest_impalad no está disponible")
    nombre = "sgmtest_" + uuid4().hex
    columnas = [Column("id", "Integer"), Column("saldo", "Double")]
    filas = [["1", "10.50"], ["2", "4.50"], ["3", "1.25"]]
    sql = "\n".join(sentencias_tipadas("default", nombre, columnas, filas))
    try:
        resultado = ejecutar_sql(sql + f"\nselect sum(saldo) as suma from default.{nombre};")
        assert resultado.returncode == 0 and "Could not execute" not in resultado.stdout
        valor = re.search(r"\|\s*(\d+(?:\.\d+)?)\s*\|", resultado.stdout)
        assert valor and Decimal(valor.group(1)) == sum(Decimal(f[1]) for f in filas)
    finally:
        ejecutar_sql(f"DROP TABLE IF EXISTS default.{nombre};")
