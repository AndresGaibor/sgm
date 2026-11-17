"""Semántica de faltantes en GROUP BY del intérprete del anillo B (plan C, tarea C-6).

Reglas de sqlproc: los faltantes de la columna de GROUP BY forman un solo grupo (p. 88); COUNT(col)
cuenta los no faltantes y COUNT(*) cuenta filas (p. 82); AVG promedia solo los no faltantes (p. 83).
"""

from __future__ import annotations

from pathlib import Path

from sgm.cli_migrar import ResultadoMigrar, _plan
from sgm.migrar.interprete import ejecutar_plan

PROGRAMA = """\
PROC SQL;
  CREATE TABLE WORK.por_region AS
  SELECT region, COUNT(*) AS n, COUNT(monto) AS n_monto, SUM(monto) AS total,
         AVG(monto) AS prom, MIN(monto) AS minimo, MAX(monto) AS maximo
  FROM WORK.ventas GROUP BY region;
QUIT;
"""

FILAS = [
    {"region": "N", "monto": "10"},
    {"region": "N", "monto": ""},
    {"region": "S", "monto": "5"},
    {"region": "S", "monto": "7"},
    {"region": "", "monto": "4"},
    {"region": "", "monto": "6"},
]


def _grupos(tmp_path: Path) -> dict[str, dict]:
    plan = _plan(PROGRAMA, "programa", ResultadoMigrar(carpeta=tmp_path))
    resultado = ejecutar_plan(plan, {"ventas": [dict(f) for f in FILAS]})
    return {fila["region"]: fila for fila in resultado["por_region"]}


def test_los_faltantes_de_la_clave_forman_un_solo_grupo(tmp_path):
    grupos = _grupos(tmp_path)

    assert set(grupos) == {"N", "S", ""}
    assert grupos[""]["n"] == "2"


def test_count_columna_cuenta_no_faltantes_y_count_estrella_cuenta_filas(tmp_path):
    grupos = _grupos(tmp_path)

    assert (grupos["N"]["n"], grupos["N"]["n_monto"]) == ("2", "1")
    assert (grupos[""]["n"], grupos[""]["n_monto"]) == ("2", "2")


def test_avg_promedia_solo_los_valores_presentes(tmp_path):
    grupos = _grupos(tmp_path)

    assert grupos["N"]["prom"] == "10"
    assert grupos["S"]["prom"] == "6"
    assert grupos[""]["prom"] == "5"


def test_sum_min_max_del_grupo_con_faltante(tmp_path):
    grupos = _grupos(tmp_path)

    assert (grupos["N"]["total"], grupos["N"]["minimo"], grupos["N"]["maximo"]) == ("10", "10", "10")
    assert (grupos["S"]["total"], grupos["S"]["minimo"], grupos["S"]["maximo"]) == ("12", "5", "7")
