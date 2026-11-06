"""Anillo A de L4: las funciones con traducción demostrada llegan al Job con nombres de muestra."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.cli_migrar import migrar

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L4"
CASOS = sorted(
    caso
    for caso in CORPUS.iterdir()
    if (caso / "programa.sas").is_file()
    and (caso / "entradas").is_dir()
    and (caso / "caso.yaml").is_file()
)


@pytest.mark.parametrize("caso", CASOS, ids=lambda caso: caso.name)
def test_las_funciones_de_l4_se_emiten_sin_pendiente_de_asignacion(caso: Path, tmp_path: Path):
    resultado = migrar(
        caso / "programa.sas",
        tmp_path / caso.name,
        muestra=caso / "entradas",
    )

    no_traducidas = [
        pendiente
        for pendiente in resultado.pendientes
        if pendiente.codigo in {"P-ASIGNACION-SIN-TRADUCIR", "P-FILTRO-SIN-TRADUCIR"}
    ]
    assert no_traducidas == []
    assert resultado.jobs
