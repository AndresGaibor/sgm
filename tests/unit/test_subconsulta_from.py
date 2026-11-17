"""Subconsulta en FROM en el intérprete del anillo B (change subconsulta-from-y-escalares, tarea 1.1)."""

from __future__ import annotations

import pytest

from sgm.cli_migrar import ResultadoMigrar, _plan
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.interprete_base import NoSoportadoEnInterprete

VENTAS = [{"id": "1", "monto": "10"}, {"id": "2", "monto": "30"}, {"id": "3", "monto": "20"}]


def _salida(programa: str, tmp_path) -> list[dict]:
    plan = _plan(programa, "programa", ResultadoMigrar(carpeta=tmp_path))
    resultado = ejecutar_plan(plan, {"ventas": [dict(f) for f in VENTAS]})
    return resultado["salida"]


def test_subconsulta_en_from_filtra_antes_de_la_consulta_de_fuera(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT s.id FROM "
        "(SELECT id, monto FROM WORK.ventas WHERE monto > 15) s;\n"
        "QUIT;\n"
    )

    assert sorted(f["id"] for f in _salida(programa, tmp_path)) == ["2", "3"]


def test_subconsulta_en_from_correlacionada_se_rechaza(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT v.id FROM WORK.ventas v WHERE v.monto > "
        "(SELECT AVG(w.monto) FROM (SELECT monto FROM WORK.ventas WHERE id = v.id) w);\n"
        "QUIT;\n"
    )

    with pytest.raises(NoSoportadoEnInterprete):
        _salida(programa, tmp_path)


def test_correlacion_se_rechaza_por_su_motivo(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT v.id FROM WORK.ventas v WHERE v.monto > "
        "(SELECT AVG(w.monto) FROM (SELECT monto FROM WORK.ventas WHERE id = v.id) w);\n"
        "QUIT;\n"
    )
    with pytest.raises(NoSoportadoEnInterprete):
        _salida(programa, tmp_path)


def test_el_emisor_no_emite_un_job_con_subconsulta_en_from(tmp_path):
    from sgm.talend_item.desde_plan import plan_a_jobs

    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.salida AS SELECT s.id FROM "
        "(SELECT id, monto FROM WORK.ventas WHERE monto > 15) s;\n"
        "QUIT;\n"
    )
    plan = _plan(programa, "programa", ResultadoMigrar(carpeta=tmp_path))

    resultado = plan_a_jobs(plan, {})

    assert resultado.jobs == []
    assert "P-OPERADOR-SIN-SOPORTE" in {p.codigo for p in resultado.pendientes}
