"""Validador estructural: lo que Studio rechaza al abrir el Job, dicho antes de abrirlo.

Cada prueba rompe una sola cosa del Job de `l2_01` y mira que el validador la nombre. Un validador
que solo dice «no» obliga a abrir Studio para saber qué pasa; por eso las pruebas comprueban también
el texto del mensaje: el nodo, la conexión y las columnas que no coinciden.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Plan
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.modelo import Columna, Conexion, Job, Metadata, ParametroContexto
from sgm.talend_item.validador import validar_job

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L2"


def _plan(caso: str = "l2_01_inner_join_clientes_ventas") -> Plan:
    texto = (CORPUS / caso / "programa.sas").read_text(encoding="utf-8")
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _job() -> Job:
    plan = _plan()
    return plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0]).jobs[0]


def _escribiendo(job: Job) -> int:
    return next(
        i for i, nodo in enumerate(job.nodos) if nodo.componente == "tFileOutputDelimited"
    )


def test_el_job_de_l2_01_es_valido():
    """El Job que sale del emisor no tiene nada que corregir: es la referencia de las demás."""
    assert validar_job(_job()) == []


def test_nombre_unico_repetido():
    job = _job()
    job.nodos.append(replace(job.nodos[0], x=999))

    problemas = validar_job(job)

    assert any("UNIQUE_NAME repetido" in p and job.nodos[0].unico in p for p in problemas)


def test_conexion_a_nodo_inexistente():
    job = _job()
    job.conexiones.append(Conexion("tMap_99", job.nodos[-1].unico, "out1"))

    problemas = validar_job(job)

    assert any("tMap_99" in p and "no está en el Job" in p for p in problemas)


def test_dos_salidas_con_el_mismo_nombre():
    """Studio no deja que un nodo tenga dos salidas llamadas `row1`: son el mismo flujo."""
    job = _job()
    ultimo = job.nodos[-1].unico
    job.conexiones.append(Conexion(job.conexiones[0].origen, ultimo, "row1"))

    problemas = validar_job(job)

    assert any("conexiones de salida llamadas 'row1'" in p for p in problemas)


def test_columnas_distintas_entre_origen_y_destino():
    job = _job()
    indice = _escribiendo(job)
    job.nodos[indice].metadatas = [Metadata("FLOW", "row1", (Columna("otra"),))]

    problemas = validar_job(job)

    assert any("lleva" in p and "espera" in p for p in problemas)
    assert any("otra" in p for p in problemas)


def test_nodo_huerfano():
    """Un `tMap` sin conexión entrante no se puede ejecutar: no tiene filas."""
    job = _job()
    job.conexiones = [c for c in job.conexiones if c.destino != "tMap_1"]

    problemas = validar_job(job)

    assert any("tMap_1" in p and "conexión entrante" in p for p in problemas)


def test_contextos_con_claves_distintas():
    job = _job()
    job.contextos["DEV"] = [*job.contextos["DEV"], ParametroContexto("ruta_de_mas")]

    problemas = validar_job(job)

    assert any("DEV" in p and "ruta_de_mas" in p for p in problemas)


def test_falta_un_grupo_de_contexto():
    job = _job()
    del job.contextos["QA"]

    problemas = validar_job(job)

    assert any("QA" in p and "grupos de contexto" in p for p in problemas)
