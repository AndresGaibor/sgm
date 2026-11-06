"""Anillo C del migrador: los Jobs que salen de `sgm migrar` compilan en Studio, en un solo lote.

Es la prueba que cierra la rebanada vertical: los anillos A (el Job) y B (el intérprete) no dicen si
Studio acepta el `.item`. Aquí se migran los casos de `L0` a `L2` que la lista viva da por completos,
se compilan todos en **una** llamada —`compilar_en_lote` copia con un sufijo nuevo y limpia
`process/` pase lo que pase— y se exige que no quede ninguno fuera.

Marca `studio`: no corre en la suite rápida. Necesita Studio abierto, el servidor `talend-mcp` con
escritura y `TALEND_MCP_DIR` y `TALEND_PROJECT` en el entorno. Si algo de eso falta, la prueba se
**salta** con el motivo a la vista: no se finge que pasó.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.studio_lote import compilar_en_lote  # noqa: E402
from corpus_lib.studio_validar import sufijo_nuevo  # noqa: E402

from sgm.backend_talend import TalendCliBackend  # noqa: E402
from sgm.backend_talend.salud import comprobar_salud  # noqa: E402
from sgm.cli_migrar import migrar  # noqa: E402

CORPUS = REPO / "tests" / "corpus"
LISTA = CORPUS / "migrar_pendientes.yaml"
NIVELES = ("L0", "L1", "L2")


def _casos_completos() -> list[Path]:
    """Casos de `L0` a `L2` que `sgm migrar` traduce enteros, según la lista viva de pendientes.

    La lista es la misma que vigila `test_migrar_corpus_aceptacion.py`: lo que se compila en Studio
    es exactamente lo que el migrador dice haber traducido, ni uno más.
    """
    pendientes = yaml.safe_load(LISTA.read_text(encoding="utf-8")) or {}
    return [
        caso
        for nivel in NIVELES
        for caso in sorted((CORPUS / nivel).iterdir())
        if (caso / "programa.sas").is_file() and caso.name not in pendientes
    ]


def _backend() -> TalendCliBackend:
    carpeta = os.environ.get("TALEND_MCP_DIR")
    proyecto = os.environ.get("TALEND_PROJECT")
    if not carpeta or not proyecto:
        pytest.skip("faltan TALEND_MCP_DIR y TALEND_PROJECT en el entorno")
    if not (Path(proyecto) / "talend.project").is_file():
        pytest.skip(f"no es un proyecto Talend (falta talend.project): {proyecto}")
    return TalendCliBackend(Path(carpeta), Path(proyecto), tiempo_max=900.0)


@pytest.mark.studio
def test_los_jobs_de_l0_a_l2_compilan_en_lote(tmp_path):
    backend = _backend()
    salud = comprobar_salud(backend)
    if not salud.ok:
        pytest.skip(f"Studio no está disponible: {salud.motivo}")

    casos = _casos_completos()
    assert casos, "no quedó ningún caso completo en L0 a L2"
    carpetas = [
        migrar(caso / "programa.sas", tmp_path / caso.name).carpeta / "process" for caso in casos
    ]

    inicio = time.perf_counter()
    resultado = compilar_en_lote(carpetas, backend.proyecto, backend, sufijo_nuevo())
    segundos = time.perf_counter() - inicio

    print(f"{len(carpetas)} Jobs en una llamada, {segundos:.1f} s")
    assert resultado.no_compilan == {}, repr(resultado.no_compilan)
    assert len(resultado.compilan) == len(carpetas)
