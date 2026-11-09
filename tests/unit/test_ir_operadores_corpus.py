"""Los constructores de `ir/operadores.py` aceptan lo que produce el lowering en el corpus L1 a L3.

Para cada operador de un plan real se reconstruye con su constructor, a partir de sus parámetros. Si
el constructor rechaza un parámetro, o su firma no coincide con la del lowering, la forma se ha
desviado y esta prueba lo avisa.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir import operadores as op  # noqa: E402

CORPUS = REPO / "tests" / "corpus"


def _casos(niveles: tuple[str, ...]):
    for nivel in niveles:
        for carpeta in sorted((CORPUS / nivel).iterdir()):
            if (carpeta / "caso.yaml").is_file():
                yield carpeta


def _plan(carpeta: Path):
    texto = (carpeta / "programa.sas").read_text(encoding="utf-8")
    return compile_file(analyze_program({"programa.sas": texto}), "programa.sas", project_base()).plan


def _reconstruir(operador):
    p = operador.params
    if operador.kind == "join":
        if "keys" in p:
            pares = [tuple(par) for par in p["keys"]]
            return op.unir(operador.id, p["join_type"], pares, p["sources"], p.get("condition"))
        return op.combinar(operador.id, p["join_type"], p["by"], p["sources"])
    if operador.kind == "filter":
        return op.filtrar(operador.id, p["expression"], p.get("outputs"))
    if operador.kind == "select":
        return op.proyectar(operador.id, p["mode"], p["names"])
    if operador.kind == "sort":
        return op.ordenar(operador.id, p["by"], p.get("descending", False), p.get("outputs"))
    if operador.kind == "dedup":
        return op.deduplicar(operador.id, p["by"], p.get("keep", "first"), p.get("outputs"))
    if operador.kind == "union":
        return op.concatenar(operador.id, p["sources"])
    if operador.kind == "aggregate":
        return op.agregar(
            operador.id,
            p["group_by"],
            p["aggregations"],
            p.get("outputs"),
            p.get("pendiente"),
            status=operador.status,
        )
    if operador.kind == "derive":
        return op.calcular(
            operador.id,
            p["assignments"],
            p.get("outputs"),
            p.get("modo"),
            p.get("declared"),
        )
    return None


@pytest.mark.parametrize("carpeta", list(_casos(("L1", "L2", "L3"))), ids=lambda c: c.name)
def test_el_constructor_reproduce_la_firma_del_lowering(carpeta: Path):
    plan = _plan(carpeta)
    for operador in plan.graph.operators():
        reconstruido = _reconstruir(operador)
        if reconstruido is None:
            continue
        assert reconstruido.signature == operador.signature, (carpeta.name, operador.kind)
