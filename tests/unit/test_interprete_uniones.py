"""Pruebas del join del intérprete del anillo B: RIGHT y FULL JOIN (plan C, tarea C-3).

Reglas de sqlproc: una fila sin pareja se conserva con las columnas del otro lado en nulo (p. 110
y p. 111), y un nulo casa con todos los nulos del mismo tipo (p. 102).
"""

from __future__ import annotations

from sgm.migrar.interprete_filas import _unir


def _llaves(tipo: str) -> dict:
    return {"join_type": tipo, "keys": [["x.k", "y.k"]]}


def test_full_join_conserva_las_filas_sin_pareja_de_los_dos_lados():
    izquierda = [{"k": 1, "va": "x1"}, {"k": None, "va": "x3"}]
    derecha = [{"k": None, "vb": "y4"}, {"k": None, "vb": "y5"}, {"k": 3, "vb": "y3"}]

    resultado = _unir(izquierda, derecha, _llaves("full"))

    assert [(f.get("va"), f.get("vb")) for f in resultado] == [
        ("x1", None),
        ("x3", "y4"),
        ("x3", "y5"),
        (None, "y3"),
    ]


def test_right_join_no_pierde_filas_de_la_derecha():
    izquierda = [{"k": 1, "va": "x1"}, {"k": 2, "va": "x2"}]
    derecha = [{"k": 2, "vb": "y2"}, {"k": 3, "vb": "y3"}]

    resultado = _unir(izquierda, derecha, _llaves("right"))

    assert [(f.get("va"), f.get("vb")) for f in resultado] == [
        ("x2", "y2"),
        (None, "y3"),
    ]


def test_un_nulo_casa_con_todos_los_nulos_del_mismo_tipo():
    izquierda = [{"k": None, "va": "x"}]
    derecha = [{"k": None, "vb": "p"}, {"k": None, "vb": "q"}]

    resultado = _unir(izquierda, derecha, _llaves("inner"))

    assert [f["vb"] for f in resultado] == ["p", "q"]


def test_left_join_sigue_igual_que_antes():
    izquierda = [{"k": 1, "va": "x1"}, {"k": 2, "va": "x2"}]
    derecha = [{"k": 2, "vb": "y2"}]

    resultado = _unir(izquierda, derecha, _llaves("left"))

    assert [(f["va"], f.get("vb")) for f in resultado] == [("x1", None), ("x2", "y2")]
