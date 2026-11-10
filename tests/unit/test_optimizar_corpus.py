"""El plan optimizado calcula lo mismo que el SAS: la fusión de pasos no cambia ningún resultado.

Para cada caso del corpus en el que el optimizador cambió el diseño, el plan optimizado se ejecuta
con el intérprete sobre las entradas del caso y se compara con `esperado/`. Una tabla intermedia
que el optimizador quitó ya no se puede comparar, y no hace falta: lo que tiene que coincidir es lo
que el programa entrega. Varios casos declaran como salida una tabla de `WORK` que solo lee el
paso siguiente (`aceptadas` en `l2_15`, `base_lealtad` en `l5_11`): el Job no la escribe.
"""

from __future__ import annotations

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.desplegar import plan_desplegado
from sgm.migrar.interprete import ejecutar_plan
from sgm.optimizar import optimizar
from tests.unit.test_migrar_corpus_anillo_b import (
    CORPUS,
    ESTADOS,
    NIVELES,
    _entradas,
    _esperado,
    casos,
)

# Caso -> motivo por el que el intérprete no ejecuta su plan, optimizado o no.
CONOCIDOS: dict[str, str] = {
    "l2_15_validacion_en_cascada": (
        "el intérprete no expande `t.*` tras un JOIN (el mismo hueco del anillo B sin optimizar)"
    ),
}


def _optimizado(caso):
    plan = compile_file(
        analyze_program({"p.sas": caso.programa.read_text(encoding="utf-8")}),
        "p.sas",
        project_base(),
    ).plan
    plan, _ = plan_desplegado(plan)
    return optimizar(plan)


def _casos():
    for nivel in NIVELES:
        for caso in casos.casos_de_nivel(CORPUS, nivel):
            if caso.estado in ESTADOS and _optimizado(caso)[1].decisiones:
                marca = []
                if caso.nombre in CONOCIDOS:
                    marca = [pytest.mark.xfail(strict=True, reason=CONOCIDOS[caso.nombre])]
                yield pytest.param(caso, id=f"{nivel}/{caso.nombre}", marks=marca)


@pytest.mark.parametrize("caso", list(_casos()))
def test_el_plan_optimizado_da_lo_que_el_sas(caso):
    plan, informe = _optimizado(caso)
    quitadas = {d.tabla for d in informe.decisiones if d.tabla}

    salidas = ejecutar_plan(plan, _entradas(caso))

    problemas = [
        problema
        for tabla in caso.salidas
        if tabla.lower() not in quitadas
        for problema in _esperado(caso, tabla, salidas.get(tabla.lower(), []))
    ]
    assert problemas == []

