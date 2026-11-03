"""Diseño de Jobs como artefacto: joblets por grupo, joblet de contexto y Job padre.

Compone piezas que ya existen: el plan compilado (`sgm.compile`), los hechos (`sgm.facts`) y el
generador de diseño (`sgm.generador`). No modifica el plan ni la guía: el diseño se revisa aparte
contra el diseño de referencia del equipo, en `docs/`.
"""

from __future__ import annotations

from sgm.facts.project import facts_for_project
from sgm.generador import diseno_del_job
from sgm.redaction import redact


def diseno_de_programa(programa: str, texto: str, plan) -> dict:
    """Diseño de un programa a partir de su texto y de su `Plan` ya compilado.

    El texto se redacta antes de extraer los hechos, igual que en la compilación: ningún valor de
    credencial entra en el artefacto.
    """
    limpio = redact(texto, programa)
    hechos = facts_for_project({programa: limpio})[programa]
    return {
        "programa": programa,
        **diseno_del_job(list(plan.graph.operators()), hechos, limpio.splitlines()),
    }
