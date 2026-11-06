"""`col [NOT] IN (SELECT k ...)` se baja a un cruce de existencia, no a una condición de texto."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.sql_tree import build
from sgm.migrar.interprete import ejecutar_plan

IMPORTAR = (
    "PROC IMPORT DATAFILE='.../{0}.csv' OUT=WORK.{0} DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
)
CLIENTES = [{"id": "1", "n": "a"}, {"id": "2", "n": "b"}, {"id": "3", "n": "c"}]
# El cliente 1 compra dos veces (no debe salir repetido) y hay una venta sin cliente (faltante).
VENTAS = [
    {"id": "1", "m": "900"},
    {"id": "1", "m": "800"},
    {"id": "2", "m": "10"},
    {"id": "", "m": "700"},
]


def _plan(condicion: str):
    texto = (
        IMPORTAR.format("clientes")
        + IMPORTAR.format("ventas")
        + "PROC SQL;\n  CREATE TABLE WORK.r AS\n  SELECT c.id, c.n FROM WORK.clientes c\n"
        + f"  WHERE {condicion};\nQUIT;\n"
    )
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _ids(plan) -> list[str]:
    return sorted(
        fila["id"] for fila in ejecutar_plan(plan, {"clientes": CLIENTES, "ventas": VENTAS})["r"]
    )


def test_la_subconsulta_simple_sale_del_where():
    spec = build(
        "SELECT c.id FROM clientes c WHERE c.id NOT IN (SELECT v.id FROM ventas v WHERE v.m > 5)"
        " AND c.n = 'a'"
    ).selects[0]

    assert spec.where == "c.n = 'a'"
    assert [(s.column, s.negate, s.key) for s in spec.semis] == [("c.id", True, "v.id")]
    assert spec.subqueries is False


def test_una_subconsulta_con_cruce_se_queda_como_estaba():
    spec = build(
        "SELECT c.id FROM clientes c WHERE c.id IN (SELECT v.id FROM ventas v JOIN x ON v.k = x.k)"
    ).selects[0]

    assert spec.semis == []
    assert spec.subqueries is True


def test_in_deja_las_filas_con_pareja_y_sin_repetir():
    assert _ids(_plan("c.id IN (SELECT v.id FROM WORK.ventas v WHERE v.m > 500)")) == ["1"]


def test_in_sin_filtro_no_duplica_al_cliente_que_compra_dos_veces():
    assert _ids(_plan("c.id IN (SELECT v.id FROM WORK.ventas v)")) == ["1", "2"]


def test_not_in_deja_las_filas_sin_pareja():
    assert _ids(_plan("c.id NOT IN (SELECT v.id FROM WORK.ventas v WHERE v.m > 500)")) == ["2", "3"]
