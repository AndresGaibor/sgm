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


class _Builder:
    def __init__(self) -> None:
        self.ops: list[tuple[str, dict, str]] = []

    def op(self, kind, params, ev, *, status="soportado", notes=None, placement=None):
        self.ops.append((kind, params, status))
        return Operator(id=f"b{len(self.ops)}", kind=kind, params=params)


def test_op_validado_con_builder_usa_el_constructor_o_el_legado() -> None:
    from sgm.ir import operadores
    from sgm.ir.pasos import op_validado

    builder = _Builder()
    op_validado(builder, lambda: operadores.filtrar("_", "x > 1"), "filter", {"expression": "x > 1"}, None)
    op_validado(builder, lambda: operadores.filtrar("_", ""), "filter", {"expression": ""}, None)
    assert builder.ops == [
        ("filter", {"expression": "x > 1"}, "soportado"),
        ("filter", {"expression": ""}, "soportado"),
    ]



def test_sentencias_where_keep_y_rename_del_data_step_pasan_por_los_constructores() -> None:
    """Regresión: `_statement_op` de `lower_data.py` pasa la evidencia como lista a los constructores.
    Sin la lista, un WHERE, un KEEP o un RENAME rompía el lowering (lo hacía en el hito 213m)."""
    from sgm.frontend.datastep import DsStatement
    from sgm.ir.builder import Builder
    from sgm.ir.lower_data_asignaciones import _statement_op
    from sgm.ir.models import Evidence, Graph

    ev = Evidence(file="p.sas", line_start=1, line_end=1, label=None)
    b = Builder(Graph())
    where = DsStatement(kind="where", text="where x > 1;", line=1, fields={"expression": "x > 1"})
    op = _statement_op(where, "where", None, ev, b, [])
    assert op.kind == "filter"
    assert op.params == {"expression": "x > 1"}
    assert op.evidence == [ev]

    keep = DsStatement(kind="keep", text="keep X Y;", line=2, fields={"names": ["X", "Y"]})
    op = _statement_op(keep, "keep", None, ev, b, [])
    assert op.kind == "select"
    assert op.params == {"mode": "keep", "names": ["x", "y"]}

    rename = DsStatement(kind="rename", text="rename x=z;", line=3, fields={"pairs": [("x", "z")]})
    op = _statement_op(rename, "rename", None, ev, b, [])
    assert op.kind == "rename"
    assert op.params == {"pairs": [["x", "z"]]}
