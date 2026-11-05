"""Tests de la sección 3 (Jobs emitidos y componentes) y de su conteo con el emisor real."""

from __future__ import annotations

from functools import lru_cache

from sgm.proceso.render_md import TITULOS
from sgm.proceso.secciones_jobs import (
    ESTADO_ESQUELETO,
    ESTADO_PARCIAL,
    LIMITE_COMPONENTES,
    componentes_emitidos,
    seccion_jobs,
)
from tests.conformidad.cargador import RAIZ

PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
DECISIONES = RAIZ / "decisiones"
JOBS = {
    "job_exogena_depositos",
    "job_producto",
    "job_totales",
    "job_conciliacion",
}


def test_seccion_jobs_distingue_esqueleto_de_lógica_parcial() -> None:
    seccion = seccion_jobs({"job_conciliacion": 1, "job_producto": 21})
    assert seccion["job_conciliacion"]["estado"] == ESTADO_ESQUELETO
    assert seccion["job_producto"]["estado"] == ESTADO_PARCIAL
    assert seccion["job_producto"]["componentes"] == "21"


def test_seccion_jobs_marca_lo_que_pasa_del_limite() -> None:
    seccion = seccion_jobs({"dentro": LIMITE_COMPONENTES, "fuera": LIMITE_COMPONENTES + 1})
    assert seccion["dentro"]["frente al límite"].startswith("dentro del límite")
    assert seccion["fuera"]["frente al límite"].startswith("por encima del límite")


def test_seccion_jobs_sin_jobs_no_inventa_filas() -> None:
    assert seccion_jobs({}) == {}


def test_titulo_de_la_seccion_3_dice_que_son_jobs() -> None:
    assert TITULOS["3"] == "Jobs emitidos y componentes"


@lru_cache(maxsize=1)
def _conteo() -> dict[str, int]:
    return componentes_emitidos(
        PROGRAMA,
        DECISIONES / f"{PROGRAMA.stem}.agrupacion.yaml",
        DECISIONES / f"{PROGRAMA.stem}.diseno.yaml",
        DECISIONES / f"{PROGRAMA.stem}.jobs.yaml",
    )


def test_componentes_emitidos_cuenta_cada_job_del_programa_grande() -> None:
    conteo = _conteo()
    assert set(conteo) == JOBS
    assert all(componentes >= 1 for componentes in conteo.values())


def test_el_job_producto_del_programa_grande_supera_el_limite_del_diseno() -> None:
    # Hecho medido y no un objetivo: el límite de 20 del manual todavía no se cumple.
    assert _conteo()["job_producto"] > LIMITE_COMPONENTES
