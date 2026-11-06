"""Una macro llamada varias veces se escribe en línea: cada llamada con sus nombres, sin perder nada."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.desplegar import plan_desplegado
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.migrar.interprete import ejecutar_plan
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.validador import validar_job

IMPORTAR = (
    "PROC IMPORT DATAFILE='.../{0}.csv' OUT=WORK.{0} DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
)
PROGRAMA = (
    IMPORTAR.format("datos_a")
    + IMPORTAR.format("datos_b")
    + "%macro activos(p);\nPROC SQL;\n  CREATE TABLE WORK.res_&p. AS\n"
    "  SELECT id, saldo FROM WORK.datos_&p. WHERE saldo >= 100;\nQUIT;\n%mend activos;\n"
    "%activos(a);\n%activos(b);\n"
)


def _plan():
    return compile_file(analyze_program({"p.sas": PROGRAMA}), "p.sas", project_base()).plan


def test_la_pasada_de_plantillas_guarda_lo_que_sustituye():
    plan = _plan()

    iterates = [op for op in plan.graph.operators() if op.kind == "iterate"]

    assert len(iterates) == 1
    guardado = plan.iteraciones[iterates[0].id]
    assert len(guardado["operadores"]) >= 6  # lectura, mapa y escritura, por dos llamadas
    assert guardado["aristas"]


def test_desplegar_devuelve_los_operadores_y_quita_el_iterate():
    plan = _plan()

    desplegado, ids = plan_desplegado(plan)

    assert len(ids) == 1
    assert not any(op.kind == "iterate" for op in desplegado.graph.operators())
    assert any(op.kind == "iterate" for op in plan.graph.operators())  # el original no se toca
    assert len(desplegado.graph) > len(plan.graph)


def test_cada_llamada_de_la_macro_da_su_job_y_su_resultado():
    plan = _plan()
    filas = [{"id": "1", "saldo": "500"}, {"id": "2", "saldo": "5"}]

    salida = ejecutar_plan(plan, {"datos_a": filas, "datos_b": filas[:1]})

    assert [f["id"] for f in salida["res_a"]] == ["1"]
    assert [f["id"] for f in salida["res_b"]] == ["1"]


def test_el_job_de_las_dos_llamadas_es_valido():
    plan = _plan()
    desplegado, _ = plan_desplegado(plan)
    tablas, _ = esquemas_de_entrada(desplegado, {})

    resultado = plan_a_jobs(plan, tablas)

    assert all(validar_job(job) == [] for job in resultado.jobs)
    iterate = next(op.id for op in plan.graph.operators() if op.kind == "iterate")
    assert iterate in resultado.visitados  # la plantilla se visitó, desplegada
