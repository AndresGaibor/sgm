"""Anillo C del migrador: L0–L2 completos y los casos L4 enfocados compilan en un lote.

Es la prueba que cierra la rebanada vertical: los anillos A (el Job) y B (el intérprete) no dicen si
Studio acepta el `.item`. Aquí se migran los casos L0–L2 que la lista viva da por completos y los
casos L4 de `COMPRESS`/`SCAN` incluidos en este alcance,
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
NIVELES = ("L0", "L1", "L2", "L4")
L4_VALIDAR_EN_STUDIO = {
    "l4_04_compress_blancos",
    "l4_05_compress_lista_caracteres",
    "l4_06_compress_modificador_k",
    "l4_07_compress_clase_digitos",
    "l4_08_compress_ignora_mayusculas",
    "l4_14_scan_palabra",
    "l4_15_scan_delimitador_fuera_de_rango",
}


def _casos_completos() -> list[Path]:
    """Casos completos de L0–L2 y L4 seleccionados, con muestras para demostrar cabeceras.

    Para L0–L2 se respeta la lista viva de pendientes; L4 cubre las funciones de texto de MG-03 y
    usa la cabecera de muestra para completar nombres que el SAS no enumera.
    """
    pendientes = yaml.safe_load(LISTA.read_text(encoding="utf-8")) or {}
    return [
        caso
        for nivel in NIVELES
        for caso in sorted((CORPUS / nivel).iterdir())
        if (caso / "programa.sas").is_file()
        and caso.name not in pendientes
        and (nivel != "L4" or caso.name in L4_VALIDAR_EN_STUDIO)
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
def test_los_jobs_completos_y_l4_en_alcance_compilan_en_lote(tmp_path):
    backend = _backend()
    salud = comprobar_salud(backend)
    if not salud.ok:
        pytest.skip(f"Studio no está disponible: {salud.motivo}")

    casos = _casos_completos()
    assert casos, "no quedó ningún caso completo en L0 a L4"
    carpetas = [
        migrar(
            caso / "programa.sas",
            tmp_path / caso.name,
            muestra=caso / "entradas" if (caso / "entradas").is_dir() else None,
        ).carpeta
        / "process"
        for caso in casos
    ]

    inicio = time.perf_counter()
    resultado = compilar_en_lote(carpetas, backend.proyecto, backend, sufijo_nuevo())
    segundos = time.perf_counter() - inicio

    print(f"{len(carpetas)} Jobs en una llamada, {segundos:.1f} s")
    assert resultado.no_compilan == {}, repr(resultado.no_compilan)
    assert len(resultado.compilan) == len(carpetas)
