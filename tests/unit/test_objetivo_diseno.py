"""Objetivo: la salida automática se acerca a `docs/diseno-talend-exogena-depositos.md`.

Estas pruebas codifican las metas medibles que el diseño de referencia implica para el archivo
`client_large.sas`. Están marcadas como `xfail` mientras la brecha exista: el informe de cada
ejecución muestra cuánto falta, y pasan a verde cuando se alcanza la meta. Ver
`docs/automatizacion/06-brecha-con-diseno.md`.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest

from sgm.compile import compile_project

CLIENT_LARGE = Path(__file__).resolve().parents[1] / "fixtures" / "sas" / "client" / "client_large.sas"
META_COMPONENTES = 100  # el diseño tiene unos 80; margen de 20
META_SUBJOBS = 40
META_LLAMADAS = 10
META_JOBS = 6  # padre, cuatro etapas y un joblet de referencia


@lru_cache(maxsize=1)
def _plan():
    texto = CLIENT_LARGE.read_text(encoding="utf-8-sig", errors="replace")
    compilados, _ = compile_project({CLIENT_LARGE.name: texto})
    return compilados[CLIENT_LARGE.name].plan


def _componentes_reales(plan) -> int:
    return sum(
        1
        for op in plan.graph.operators()
        if (op.component or {}).get("name") not in (None, "none", "-", "tRunJob")
    )


def _llamadas(plan) -> int:
    return sum(1 for op in plan.graph.operators() if op.kind == "iterate")


def _jobs(plan) -> int:
    return len(plan.jobs) + sum(len(j.children) for j in plan.jobs)


@pytest.mark.xfail(reason="brecha: componentes reales; el diseño tiene unos 80", strict=False)
def test_componentes_reales_cerca_del_diseno() -> None:
    assert _componentes_reales(_plan()) <= META_COMPONENTES


@pytest.mark.xfail(reason="brecha: subjobs; el diseño usa uno por etapa", strict=False)
def test_subjobs_cerca_del_diseno() -> None:
    assert sum(len(j.subjobs) for j in _plan().jobs) <= META_SUBJOBS


@pytest.mark.xfail(reason="brecha: una llamada por instancia en vez de un bucle", strict=False)
def test_llamadas_cerca_del_diseno() -> None:
    assert _llamadas(_plan()) <= META_LLAMADAS


@pytest.mark.xfail(reason="brecha: Jobs hijos; el diseño tiene un Job por etapa", strict=False)
def test_jobs_cerca_del_diseno() -> None:
    assert _jobs(_plan()) <= META_JOBS


@pytest.mark.xfail(reason="brecha: el plan no declara variables de contexto", strict=False)
def test_contextos_declarados() -> None:
    plan = _plan()
    variables = sum(len(j.contexts) for j in plan.jobs)
    assert variables >= 3


@pytest.mark.xfail(reason="brecha: el SQL no se empuja a la base en un solo tDBInput", strict=False)
def test_sql_empujado_a_la_base() -> None:
    plan = _plan()
    en_base = Counter(
        (op.placement or "").split(":")[0] for op in plan.graph.operators()
    )["db"]
    assert en_base >= 50
