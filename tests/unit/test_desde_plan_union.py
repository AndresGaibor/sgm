"""B-10: `SET a b;` con columnas distintas se alinea por nombre antes de `tUnite` (lestmtsref, p. 343).

Cada entrada que no trae las columnas de la unión pasa por un `tMap` que emite el esquema de la unión,
con `null` donde la entrada no tiene la columna. Las entradas con el mismo esquema van directo a `tUnite`.
"""

from __future__ import annotations

from types import SimpleNamespace

from sgm.talend_item.desde_plan_union import nodo_union
from sgm.talend_item.modelo import Columna

A = [Columna("id"), Columna("x")]
B = [Columna("id"), Columna("y")]


def _op(**params):
    return SimpleNamespace(params=params)


def _nombres(columnas) -> list[str]:
    return [c.nombre for c in columnas]


def _contador():
    numeros = iter(range(1, 100))
    return lambda: f"tMap_{next(numeros)}"


def test_columnas_distintas_alinean_cada_entrada_con_un_tmap():  # lestmtsref, p. 343
    resultado = nodo_union(_op(), [A, B], "tUnite_1", 0, None, None, _contador())
    assert resultado.pendientes == []
    assert resultado.nodo is not None and resultado.nodo.componente == "tUnite"
    assert sorted(resultado.alineados) == [0, 1]
    for tmap in resultado.alineados.values():
        assert tmap.componente == "tMap"
        assert _nombres(tmap.metadatas[0].columnas) == ["id", "x", "y"]


def test_mismo_esquema_va_directo_a_tunite():
    resultado = nodo_union(_op(), [A, A], "tUnite_1", 0, None, None, _contador())
    assert resultado.pendientes == []
    assert resultado.alineados == {}
    assert resultado.nodo is not None and resultado.nodo.componente == "tUnite"


def test_union_sin_all_sigue_pendiente():
    resultado = nodo_union(_op(all=False), [A, B], "tUnite_1", 0, None, None, _contador())
    assert resultado.nodo is None
    assert [p.codigo for p in resultado.pendientes] == ["P-UNION-SIN-ALL"]
