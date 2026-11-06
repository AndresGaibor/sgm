"""Contextos por entorno: las rutas salen de los nodos y quedan como variables de contexto.

El objetivo es que el `.item` de DEV y el de PROD sean el mismo archivo: si la ruta está dentro de un
componente, no lo son. La prueba mira el Job armado y el `.item` ya serializado, porque un cambio en
la escritura también rompería el contrato.
"""

from __future__ import annotations

import re
from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Plan
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_contextos import GRUPOS, contextos_de_plan, rutas_de_plan
from sgm.talend_item.item import render_item
from sgm.talend_item.modelo import Job

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L2"


def _plan(caso: str = "l2_01_inner_join_clientes_ventas") -> Plan:
    texto = (CORPUS / caso / "programa.sas").read_text(encoding="utf-8")
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _job(plan: Plan) -> Job:
    return plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0]).jobs[0]


def _rutas_en_nodos(job: Job) -> list[str]:
    """Los `FILENAME` de todos los nodos, en orden: uno por componente de archivo."""
    return [
        str(valor)
        for nodo in job.nodos
        for parametro in nodo.parametros
        if isinstance(parametro, tuple)
        for _, nombre, valor, _ in [parametro]
        if nombre == "FILENAME"
    ]


def test_cuatro_grupos_con_las_mismas_claves():
    contextos = contextos_de_plan(_plan())

    assert tuple(contextos) == GRUPOS
    claves = [[parametro.nombre for parametro in grupo] for grupo in contextos.values()]
    assert claves[0] == ["ruta_clientes", "ruta_ventas", "ruta_ventas_con_nombre"]
    assert all(iguales == claves[0] for iguales in claves)


def test_el_literal_solo_va_al_grupo_por_omision():
    contextos = contextos_de_plan(_plan())

    assert contextos["Default"][0].valor == ".../entradas/clientes.csv"
    for grupo in GRUPOS[1:]:
        assert {parametro.valor for parametro in contextos[grupo]} == {""}


def test_ruta_literal_no_queda_en_el_nodo():
    """La ruta no queda en ningún componente: va al contexto `Default`, que es donde se cambia.

    El `.item` sí contiene el literal, una sola vez y en el bloque de contexto; lo que no puede es
    quedar dentro de un `FILENAME`, porque entonces el Job de DEV y el de PROD no serían el mismo.
    """
    job = _job(_plan())

    assert set(_rutas_en_nodos(job)) == {
        "context.ruta_clientes",
        "context.ruta_ventas",
        "context.ruta_ventas_con_nombre",
    }
    texto = render_item(job)
    assert "context.ruta_clientes" in texto
    assert not re.search(r'name="FILENAME" value="[^"]*entradas/', texto)


def test_el_marcador_de_ruta_con_puntos_suspensivos_se_conserva_como_valor_por_omision():
    """El `...` del corpus es el marcador de «la carpeta del caso»: se copia tal cual, sin resolverlo."""
    rutas = rutas_de_plan(_plan())

    assert rutas[".../entradas/clientes.csv"] == "ruta_clientes"
    assert ".../salida/ventas_con_nombre.csv" in rutas


def test_sin_secretos():
    job = _job(_plan())

    for grupo in job.contextos.values():
        for parametro in grupo:
            assert not re.search(r"pass|pwd|secret|token|clave", parametro.nombre, re.I)
            assert parametro.valor == "" or parametro.nombre.startswith("ruta_")
