"""Cada salida de un `tMap` tiene un esquema con su mismo nombre.

Si la salida se llama `row2` y su esquema `out3`, Studio carga el Job pero avisa «Some errors
appear after the migration in the following connections: row2» (hito 191, `l6_18`).
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.talend_item.validador import validar_job

CASO = Path("tests/corpus/L6/l6_18_output_condicional_sin_destino_con_continuacion")


def _tmaps(texto: str) -> dict[str, tuple[set[str], set[str]]]:
    """Por cada `tMap`: (nombres de `outputTables`, nombres de esquemas FLOW de salida)."""
    resultado: dict[str, tuple[set[str], set[str]]] = {}
    for bloque in re.findall(r"<node [^>]*componentName=\"tMap\".*?</node>", texto, re.S):
        unico = re.search(r'name="UNIQUE_NAME"[^>]*value="(\w+)"', bloque).group(1)  # type: ignore[union-attr]
        salidas = set(re.findall(r'<outputTables[^>]*\bname="([^"]+)"', bloque))
        esquemas = set(re.findall(r'<metadata connector="FLOW" name="([^"]+)"', bloque))
        resultado[unico] = (salidas, esquemas)
    return resultado


def test_los_esquemas_de_un_tmap_llevan_el_nombre_de_sus_salidas(tmp_path: Path) -> None:
    migrar(CASO / "programa.sas", tmp_path / "out", muestra=CASO / "entradas")
    texto = next(tmp_path.rglob("*.item")).read_text(encoding="utf-8")
    tmaps = _tmaps(texto)
    assert tmaps, "el caso debe emitir al menos un tMap"
    for unico, (salidas, esquemas) in tmaps.items():
        assert salidas <= esquemas, (unico, salidas, esquemas)


def test_el_validador_rechaza_una_salida_sin_esquema(tmp_path: Path) -> None:
    resultado = migrar(CASO / "programa.sas", tmp_path / "out", muestra=CASO / "entradas")
    job = resultado.jobs[0]
    assert validar_job(job) == []
    tmap = next(n for n in job.nodos if n.componente == "tMap")
    tmap.metadatas = [
        replace(bloque, nombre="sin_esquema") if bloque.nombre == "row2" else bloque
        for bloque in tmap.metadatas or []
    ]
    problemas = validar_job(job)
    assert any("'row2'" in problema and "esquema" in problema for problema in problemas), problemas
