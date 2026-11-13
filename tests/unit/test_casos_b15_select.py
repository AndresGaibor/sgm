"""B-15: los casos L4 de `SELECT` y `DELETE` (l4_21 a l4_23) coinciden con su `esperado/`.

Cada caso se corre con el intérprete de referencia (capa B) y se compara con el CSV escrito a mano desde la
regla de SAS. Las invariantes de `caso.yaml` se comprueban aparte. Las citas: `lestmtsref`, p. 340 (SELECT) y
p. 77 (DELETE); `lrcon` no tiene entrada para `SELECT` ni para `DELETE` en su índice.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.invariantes import comprobar  # noqa: E402

from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.migrar.interprete import ejecutar_plan  # noqa: E402

CASOS = ["l4_21_select_when_con_otherwise", "l4_22_select_sin_expresion", "l4_23_delete_condicional"]
CORPUS = REPO / "tests" / "corpus" / "L4"


def _csv(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as f:
        return [{k.lower(): v for k, v in fila.items()} for fila in csv.DictReader(f)]


def _numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return str(valor).strip()


@pytest.mark.parametrize("nombre", CASOS)
def test_invariantes_del_caso(nombre: str) -> None:
    caso = cargar_caso(CORPUS / nombre)
    assert comprobar(list(caso.invariantes), [caso.esperado, caso.entradas], caso.tolerancia) == []


@pytest.mark.parametrize("nombre", CASOS)
def test_el_intérprete_coincide_con_el_esperado(nombre: str) -> None:
    carpeta = CORPUS / nombre
    programa = (carpeta / "programa.sas").read_text(encoding="utf-8")
    plan = compile_file(analyze_program({"p.sas": programa}), "p.sas", project_base()).plan
    entrada = next((carpeta / "entradas").glob("*.csv"))
    tabla = "valores_" + nombre.split("_")[0] + "_" + nombre.split("_")[1]
    obtenido = ejecutar_plan(plan, {tabla: _csv(entrada)})
    salida = next(p for p in (carpeta / "esperado").glob("*.csv"))
    clave = salida.stem.lower()
    esperadas = _csv(salida)
    filas = obtenido[clave]
    assert len(filas) == len(esperadas), f"{nombre}: {len(filas)} filas, se esperaban {len(esperadas)}"
    for real, esperada in zip(filas, esperadas, strict=True):
        # Los nombres de variable de SAS no distinguen mayúsculas: se comparan en minúsculas.
        real = {k.lower(): v for k, v in real.items()}
        for columna, valor in esperada.items():
            assert _numero(real.get(columna)) == _numero(valor), f"{nombre}: {columna}"
