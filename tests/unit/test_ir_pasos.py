"""`paso` usa los parámetros del constructor o, si lo rechaza, la forma legado (B-5)."""

from __future__ import annotations

from sgm.ir.models import Operator
from sgm.ir.pasos import paso


class _Cadena:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, dict, str]] = []

    def step(self, kind, params, previous, status="soportado"):
        self.llamadas.append((kind, params, status))
        return Operator(id=f"op{len(self.llamadas)}", kind=kind, params=params)


class _Constructor:
    def __init__(self, params):
        self.params = params


def _previo() -> Operator:
    return Operator(id="previo", kind="read", params={})


def test_usa_los_parametros_del_constructor_si_acepta() -> None:
    cadena = _Cadena()
    resultado = paso(cadena, "filter", {"legado": 1}, lambda: _Constructor({"expression": "x > 1"}), _previo())
    assert cadena.llamadas == [("filter", {"expression": "x > 1"}, "soportado")]
    assert resultado.params == {"expression": "x > 1"}


def test_usa_la_forma_legado_si_el_constructor_rechaza() -> None:
    def rechaza():
        raise ValueError("sin columnas")

    cadena = _Cadena()
    paso(cadena, "sort", {"legado": True}, rechaza, _previo(), status="pendiente")
    assert cadena.llamadas == [("sort", {"legado": True}, "pendiente")]
