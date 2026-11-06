"""Anillo B del corpus: el intérprete del plan calcula lo mismo que el SAS de referencia.

Para cada caso de `L0`, `L1` y `L2` en estado `traducible` o `revisado`, se ejecuta el plan sobre las
entradas del caso y se compara con `esperado/`, con la tolerancia y el orden que declara su
`caso.yaml`. No se compara con el Job ni con Studio: se compara con el SAS, que es la referencia.

Los casos que el intérprete todavía no sabe ejecutar están en `CONOCIDOS` con el motivo, y se marcan
`xfail(strict=True)`: si uno empieza a pasar, la prueba falla y obliga a quitar la entrada. Así la
lista no envejece en silencio.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib import caso as casos  # noqa: E402
from corpus_lib.csv_tabla import Tabla, comparar_con_guardado, leer_entradas  # noqa: E402

CORPUS = REPO / "tests" / "corpus"
NIVELES = ("L0", "L1", "L2", "L3", "L4", "L5", "L6")
ESTADOS = ("traducible", "revisado")

# Caso -> motivo por el que el intérprete todavía no lo ejecuta. Las entradas son de dos clases: pasos
# que el intérprete no implementa (y que al implementarlos harán fallar la prueba, como debe ser), y
# dos huecos del plan que no son del intérprete y están anotados en PROGRESS.md.
_NO_LO_EJECUTA = "el intérprete no ejecuta el paso '{paso}' todavía"
CONOCIDOS: dict[str, str] = {
    # Huecos del plan, no del intérprete.
    "l2_12_auto_join_misma_ciudad": (
        "el plan pierde el alias del auto-unión: las dos referencias quedan 'id_cliente < id_cliente'"
    ),
    # Pasos que el intérprete todavía no ejecuta.
    "l3_01_count_star_vs_count_col": (
        "una expresión sobre agregados (COUNT(*) - COUNT(saldo)) no es FUNCION(columna)"
    ),
    "l3_07_total_origen_y_salida": (
        "tres SELECT con WHERE sobre la misma tabla se funden en un map con ramas sin salidas"
    ),
    "l3_09_conciliacion_diferencia_plantada": "subconsulta escalar dentro del SELECT",

    "l5_06_sysfunc_upcase": "%let con %sysfunc: la macro dinámica queda como unsupported (macros)",
    "l5_08_str_filtro_completo": "la macro variable &FILTRO llega a la expresión sin resolver",
    "l5_09_into_primer_fila": "SELECT INTO deja la macro variable &ANIO sin resolver en la consulta",
    "l2_15_validacion_en_cascada": "el intérprete no expande `t.*` tras un JOIN: no sabe qué columnas son de t",
}


def _casos():
    for nivel in NIVELES:
        for caso in casos.casos_de_nivel(CORPUS, nivel):
            if caso.estado not in ESTADOS:
                continue
            marca = []
            if caso.nombre in CONOCIDOS:
                marca = [pytest.mark.xfail(strict=True, reason=CONOCIDOS[caso.nombre])]
            yield pytest.param(caso, id=f"{nivel}/{caso.nombre}", marks=marca)


def _entradas(caso) -> dict[str, list[dict]]:
    return {
        nombre: [dict(zip(tabla.columnas, fila, strict=True)) for fila in tabla.filas]
        for nombre, tabla in leer_entradas(caso.entradas).items()
    }


def _esperado(caso, tabla: str, filas: list[dict]) -> list[str]:
    """Diferencias con `esperado/<tabla>.csv`, con las columnas del archivo esperado."""
    ruta = caso.esperado / f"{tabla}.csv"
    if not ruta.exists():
        return [f"{tabla}: falta {ruta.name}"]
    columnas = ruta.read_text(encoding="utf-8").splitlines()[0].split(",")
    calculada = Tabla(
        columnas,
        [
            tuple(
                next((valor for clave, valor in fila.items() if clave.lower() == columna.lower()), None)
                for columna in columnas
            )
            for fila in filas
        ],
    )
    return comparar_con_guardado(ruta, calculada, caso.tolerancia, caso.orden_relevante)


@pytest.mark.parametrize("caso", list(_casos()))
def test_el_interprete_da_lo_que_el_sas(caso):
    plan = compile_file(
        analyze_program({"p.sas": caso.programa.read_text(encoding="utf-8")}),
        "p.sas",
        project_base(),
    ).plan

    salidas = ejecutar_plan(plan, _entradas(caso))

    problemas = [
        problema
        for tabla in caso.salidas
        for problema in _esperado(caso, tabla, salidas.get(tabla.lower(), []))
    ]
    assert problemas == []
