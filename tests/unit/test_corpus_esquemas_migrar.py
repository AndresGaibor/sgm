"""Lo que emite `sgm migrar` coincide con los tipos demostrados del bloque `esquemas` de cada caso.

Solo se compara lo que el SAS demuestra (tipo distinto de `pendiente`). Un tipo pendiente no se
afirma en ningún sentido: no se exige ni se prohíbe.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import cargar_caso  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402

CORPUS = REPO / "tests" / "corpus"


def _casos_demostrados():
    for carpeta in sorted(CORPUS.glob("L*/**/caso.yaml")):
        caso = cargar_caso(carpeta.parent)
        for _tabla, columnas in (caso.extra.get("esquemas") or {}).items():
            for columna, entrada in columnas.items():
                if entrada["tipo"] != "pendiente":
                    yield pytest.param(caso, columna, entrada, id=f"{caso.nombre}-{columna}")


@pytest.mark.parametrize("caso, columna, entrada", list(_casos_demostrados()))
def test_la_salida_lleva_el_largo_que_el_sas_declara(tmp_path: Path, caso, columna, entrada):
    if "longitud" not in entrada:
        pytest.skip("el tipo demostrado no declara largo")
    resultado = migrar(caso.programa, tmp_path / "out", muestra=caso.entradas)
    columnas = [
        c
        for job in resultado.jobs
        for nodo in job.nodos
        for c in [*nodo.columnas, *[x for m in (nodo.metadatas or []) for x in m.columnas]]
        if c.nombre.lower() == columna.lower()
    ]
    assert columnas, f"{caso.nombre}: la columna {columna} no aparece en el Job"
    assert all(c.longitud == entrada["longitud"] for c in columnas), [
        (c.nombre, c.longitud) for c in columnas
    ]
