"""Anillo A de L4: las funciones con traducción demostrada llegan al Job con nombres de muestra."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from sgm.cli_migrar import migrar

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L4"
CASOS = sorted(
    caso
    for caso in CORPUS.iterdir()
    if (caso / "programa.sas").is_file()
    and (caso / "entradas").is_dir()
    and (caso / "caso.yaml").is_file()
    and yaml.safe_load((caso / "caso.yaml").read_text(encoding="utf-8")).get("estado")
    in {"traducible", "revisado"}
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


def test_los_predicados_sas_se_emiten_como_numeros_cero_o_uno(tmp_path: Path):
    caso = CORPUS / "l4_19_cmp_faltantes"
    resultado = migrar(
        caso / "programa.sas",
        tmp_path / caso.name,
        muestra=caso / "entradas",
    )
    (item,) = (resultado.carpeta / "process").glob("*.item")
    root = ET.parse(item).getroot()
    asignaciones = {
        entrada.get("name"): entrada
        for entrada in root.iter("mapperTableEntries")
        if entrada.get("name") in {"BAJO_500", "ES_FALTANTE"}
    }

    assert set(asignaciones) == {"BAJO_500", "ES_FALTANTE"}
    assert all(asignacion.get("type") == "id_Long" for asignacion in asignaciones.values())
    assert all(
        "Long.valueOf(" in asignacion.get("expression", "") for asignacion in asignaciones.values()
    )
