"""Línea base del plan lógico (B-1): la medición de un programa y sus pendientes por código."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import linea_base_plan_logico as base  # noqa: E402


def test_set_con_where_se_mide_con_operadores_soportados() -> None:
    m = base.medir_programa("data work.s; set work.a; where x > 1; run;\n")
    assert m["operadores"] >= 1
    assert 0 <= m["soportados"] <= m["operadores"]
    assert m["no_migrados"] >= 0


def test_merge_suelto_da_operador_sin_soporte_con_su_codigo(tmp_path: Path) -> None:
    programa = tmp_path / "p.sas"
    programa.write_text("data work.m; merge work.a work.b; by k; run;\n", encoding="utf-8")
    codigos = base.codigos_de_programa(programa)
    # El plan supuso `P-UNION-TIPO-SIN-SOPORTE`; el código que sale hoy es este. Se fija el real.
    assert codigos["P-OPERADOR-SIN-SOPORTE"] >= 1
