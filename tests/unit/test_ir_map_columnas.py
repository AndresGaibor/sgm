"""El operador `map` conserva la selección del SELECT y las llaves de la unión.

Sin esto el `tMap` sale vacío: `assignments: []` y `keys: []`. Las expresiones y las llaves van con
el nombre de la tabla, no con el alias del SAS, porque el `tMap` no conoce los alias.
"""

from __future__ import annotations

from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L2"


def _pasos(caso: str) -> list[dict]:
    texto = (CORPUS / caso / "programa.sas").read_text(encoding="utf-8")
    analysis = analyze_program({"p.sas": texto})
    plan = compile_file(analysis, "p.sas", project_base()).plan
    mapa = next(op for op in plan.graph.operators() if op.kind == "map")
    return mapa.params["steps"]


def _paso(pasos: list[dict], kind: str) -> dict:
    return next(paso for paso in pasos if paso["kind"] == kind)


def test_select_de_columnas_da_asignaciones():
    pasos = _pasos("l2_01_inner_join_clientes_ventas")

    assert _paso(pasos, "derive")["params"]["assignments"] == [
        {"target": "id_venta", "expression": "ventas.id_venta", "origin": "columna"},
        {"target": "nombre", "expression": "clientes.nombre", "origin": "columna"},
        {"target": "monto", "expression": "ventas.monto", "origin": "columna"},
    ]


def test_inner_join_tiene_llaves():
    unir = _paso(_pasos("l2_01_inner_join_clientes_ventas"), "join")["params"]

    assert unir["keys"] == [["ventas.id_cliente", "clientes.id_cliente"]]
    assert unir["join_type"] == "inner"


def test_left_join_conserva_el_tipo():
    unir = _paso(_pasos("l2_02_left_join_con_faltantes"), "join")["params"]

    assert unir["join_type"] == "left"
    assert unir["keys"] == [["clientes.id_cliente", "ventas.id_cliente"]]


def test_join_con_dos_llaves():
    unir = _paso(_pasos("l2_03_join_dos_columnas_en_on"), "join")["params"]

    assert unir["keys"] == [
        ["ventas.id_cliente", "metas.id_cliente"],
        ["ventas.canal", "metas.canal"],
    ]
