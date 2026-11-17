"""CREATE TABLE ... LIKE en el intérprete (plan C, C-12): el molde sale vacío y el emisor lo deja pendiente."""

from __future__ import annotations

from sgm.cli_migrar import ResultadoMigrar, _plan
from sgm.migrar.interprete import ejecutar_plan
from sgm.talend_item.desde_plan import plan_a_jobs

PROGRAMA = (
    "PROC SQL;\n"
    "  CREATE TABLE WORK.molde LIKE WORK.ventas;\n"
    "QUIT;\n"
)


def test_el_molde_queda_vacio_en_el_intérprete(tmp_path):
    plan = _plan(PROGRAMA, "programa", ResultadoMigrar(carpeta=tmp_path))

    resultado = ejecutar_plan(plan, {"ventas": [{"id": "1"}, {"id": "2"}]})

    assert resultado["molde"] == []


def test_el_emisor_no_traduce_create_like(tmp_path):
    plan = _plan(PROGRAMA, "programa", ResultadoMigrar(carpeta=tmp_path))

    resultado = plan_a_jobs(plan, {})

    assert resultado.pendientes
    assert resultado.jobs[0].nodos == [] if resultado.jobs else True
