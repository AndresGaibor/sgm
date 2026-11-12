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


_TIPO_TALEND = {"String": "id_String", "Double": "id_Double"}


@pytest.mark.parametrize("caso, columna, entrada", list(_casos_demostrados()))
def test_la_salida_lleva_el_tipo_y_el_largo_que_el_caso_declara(tmp_path: Path, caso, columna, entrada):
    """El Job que emite `sgm migrar` tiene el tipo demostrado del bloque `esquemas` (B-4)."""
    resultado = migrar(caso.programa, tmp_path / "out", muestra=caso.entradas)
    columnas = [
        c
        for job in resultado.jobs
        for nodo in job.nodos
        for c in [*nodo.columnas, *[x for m in (nodo.metadatas or []) for x in m.columnas]]
        if c.nombre.lower() == columna.lower()
    ]
    if not columnas:
        # la tabla no sale en el Job: el caso tiene pendientes de traducción (p. ej. INTO :var).
        # Que una columna no se emita no es un tipo distinto; el tipo se mide donde sí aparece.
        pytest.skip(f"{caso.nombre}: {columna} no aparece en el Job (pendientes del caso)")
    esperado = _TIPO_TALEND[entrada["tipo"]]
    assert all(c.tipo == esperado for c in columnas), [(c.nombre, c.tipo) for c in columnas]
    if "longitud" in entrada:
        assert all(c.longitud == entrada["longitud"] for c in columnas), [
            (c.nombre, c.longitud) for c in columnas
        ]
