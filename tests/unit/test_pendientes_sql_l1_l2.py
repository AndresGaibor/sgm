"""B-7: los casos `traducible` de L1 y L2 no tienen pendientes de defecto.

Cada pendiente real (sin las notas de tipo) de todos los casos de L1 y L2 tiene que estar clasificado aquí:

- `alcance`: SQL fuera del dialecto soportado, con su página de `sqlproc` que lo dice.
- `entorno`: el traductor no puede demostrarlo con lo que el repositorio sabe; hace falta un dato del
  entorno (una decisión del dueño). El caso se queda en `migrar_pendientes.yaml` con ese motivo.

Un pendiente que no esté en la tabla es un defecto y rompe la prueba.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import todos_los_casos  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402

# Notas de tipo: no son una pérdida de traducción (ver `test_migrar_corpus_aceptacion.NOTAS`).
NOTAS = frozenset({"P-TIPO-DESCONOCIDO", "P-CONFIGURACION-RESUELTA"})

CLASIFICACION: dict[tuple[str, str], tuple[str, str]] = {
    # `LZ` es una base de datos (decisión del dueño, 17 de noviembre de 2026; docs/BLOQUEOS.md, B-7).
    # Con `LZ` declarada en env/engines.json y `push_to_db` (los programas que la leen), queda un único
    # pendiente de configuración: el host, el puerto y la base del componente.
    ("l2_16_sql_en_misma_base", "P-CONEXION-BASE"): (
        "entorno",
        "LZ es una base declarada en env/engines.json; host, puerto y base se configuran por entorno",
    ),
}


def _casos() -> list:
    corpus = REPO / "tests" / "corpus"
    return [
        c
        for c in todos_los_casos(corpus)
        if c.nivel in ("L1", "L2")
    ]


@pytest.fixture(scope="module")
def pendientes_por_caso() -> dict[str, set[str]]:
    base = Path(tempfile.mkdtemp())
    salida: dict[str, set[str]] = {}
    for caso in _casos():
        resultado = migrar(caso.programa, base / caso.nombre, muestra=caso.entradas)
        salida[caso.nombre] = {p.codigo for p in resultado.pendientes if p.codigo not in NOTAS}
    return salida


def test_no_hay_pendientes_de_defecto_en_l1_y_l2(pendientes_por_caso) -> None:
    defectos = [
        (caso, codigo)
        for caso, codigos in pendientes_por_caso.items()
        for codigo in codigos
        if (caso, codigo) not in CLASIFICACION
    ]
    assert defectos == [], f"pendientes sin clasificar (defecto): {defectos}"


def test_la_clasificacion_no_guarda_pendientes_que_ya_no_existen(pendientes_por_caso) -> None:
    vivos = {(caso, codigo) for caso, codigos in pendientes_por_caso.items() for codigo in codigos}
    obsoletos = [clave for clave in CLASIFICACION if clave not in vivos]
    assert obsoletos == [], f"quitar de CLASIFICACION: {obsoletos}"
