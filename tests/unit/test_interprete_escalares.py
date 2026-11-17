"""Subconsulta escalar del WHERE en el intérprete del anillo B (plan C, C-8).

El promedio, el máximo y el conteo se calculan antes del filtro. Lo que no encaja (correlacionada,
con GROUP BY, o con más de una columna) queda como no soportado, nunca como un resultado inventado.
"""

from __future__ import annotations

from sgm.cli_migrar import ResultadoMigrar, _plan
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.interprete_base import NoSoportadoEnInterprete

VENTAS = [{"id": "1", "monto": "10"}, {"id": "2", "monto": "30"}, {"id": "3", "monto": "20"}]


def _ids(programa: str, tmp_path, filas=VENTAS) -> list[str]:
    plan = _plan(programa, "programa", ResultadoMigrar(carpeta=tmp_path))
    resultado = ejecutar_plan(plan, {"ventas": [dict(f) for f in filas]})
    return [f["id"] for f in resultado["salida"]]


def test_where_con_promedio_escalar_deja_solo_las_filas_sobre_la_media(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT id, monto FROM WORK.ventas\n"
        "  WHERE monto > (SELECT AVG(monto) FROM WORK.ventas);\n"
        "QUIT;\n"
    )
    assert _ids(programa, tmp_path) == ["2"]


def test_maximo_escalar_en_where(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT id, monto FROM WORK.ventas\n"
        "  WHERE monto = (SELECT MAX(monto) FROM WORK.ventas);\n"
        "QUIT;\n"
    )
    assert _ids(programa, tmp_path) == ["2"]


def test_escalar_correlacionada_no_se_calcula(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT id, monto FROM WORK.ventas v\n"
        "  WHERE monto > (SELECT AVG(w.monto) FROM WORK.ventas w WHERE w.id = v.id);\n"
        "QUIT;\n"
    )
    import pytest

    with pytest.raises(NoSoportadoEnInterprete):
        _ids(programa, tmp_path)


def test_escalar_con_group_by_no_se_calcula(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT id, monto FROM WORK.ventas\n"
        "  WHERE monto > (SELECT AVG(monto) FROM WORK.ventas GROUP BY id);\n"
        "QUIT;\n"
    )
    import pytest

    with pytest.raises(NoSoportadoEnInterprete):
        _ids(programa, tmp_path)
