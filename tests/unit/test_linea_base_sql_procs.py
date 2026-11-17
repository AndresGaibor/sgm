"""Pruebas de tools/linea_base_sql_procs.py (plan C, tarea C-1): línea base de SQL y procedimientos."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import linea_base_sql_procs as lb  # noqa: E402


def _caso(corpus: Path, nivel: str, nombre: str, construcciones: list[str], capa: str = "B") -> None:
    carpeta = corpus / nivel / nombre
    carpeta.mkdir(parents=True)
    (carpeta / "programa.sas").write_text("DATA WORK.x; SET WORK.y; RUN;\n", encoding="utf-8")
    lineas = "\n".join(f"  - {c}" for c in construcciones)
    (carpeta / "caso.yaml").write_text(
        f"nivel: {nivel}\nconstrucciones:\n{lineas}\ncapa: {capa}\nestado: sin_esperado\n"
        "motivo: caso de prueba de la línea base\n",
        encoding="utf-8",
    )


def test_cuenta_casos_y_pendientes_por_construccion(tmp_path):
    _caso(tmp_path, "L2", "a", ["PROC SQL", "FULL JOIN"])
    _caso(tmp_path, "L3", "b", ["PROC MEANS"])
    (tmp_path / "migrar_pendientes.yaml").write_text("a: P-FULL-JOIN-SIN-SOPORTE\n", encoding="utf-8")

    medida = lb.medir(tmp_path)

    assert medida["PROC MEANS"]["casos"] == 1
    assert medida["PROC MEANS"]["pendientes"] == {}
    assert medida["FULL JOIN"] == {"casos": 1, "pendientes": {"P-FULL-JOIN-SIN-SOPORTE": 1}}
    assert medida["PROC SQL"]["casos"] == 1


def test_solo_entran_las_construcciones_de_sql_y_procedimientos(tmp_path):
    _caso(tmp_path, "L1", "c", ["LIBNAME", "PROC SORT"])
    (tmp_path / "migrar_pendientes.yaml").write_text("", encoding="utf-8")

    medida = lb.medir(tmp_path)

    assert "PROC SORT" in medida
    assert "LIBNAME" not in medida


def test_el_pendiente_se_cuenta_por_codigo(tmp_path):
    _caso(tmp_path, "L4", "d", ["PROC SORT"])
    _caso(tmp_path, "L4", "e", ["PROC SORT"])
    (tmp_path / "migrar_pendientes.yaml").write_text(
        "d: P-OPERADOR-SIN-SOPORTE\n", encoding="utf-8"
    )

    medida = lb.medir(tmp_path)

    assert medida["PROC SORT"]["casos"] == 2
    assert medida["PROC SORT"]["pendientes"] == {"P-OPERADOR-SIN-SOPORTE": 1}
