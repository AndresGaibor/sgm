"""Constructores validados de los 14 operadores del plan lógico (MG-P1-03)."""

from __future__ import annotations

import pytest

from sgm.ir import operadores as op
from sgm.ir.models import OPERATOR_KINDS, Graph
from sgm.ir.signature import signature


def test_cada_constructor_produce_un_kind_del_modelo_con_su_firma():
    casos = [
        (op.leer("1", "WORK.a"), "read"),
        (op.leer_archivo("2", "x.csv", ["WORK.a"]), "read_file"),
        (op.escribir("3", "WORK.b"), "write"),
        (op.filtrar("4", "saldo > 0"), "filter"),
        (op.proyectar("5", "keep", ["Id", "Nombre"]), "select"),
        (op.renombrar("6", [("A", "B")]), "rename"),
        (op.calcular("7", [{"target": "x", "expression": "1"}]), "derive"),
        (op.unir("8", "left", [("a.id", "b.id")], ["WORK.a", "WORK.b"]), "join"),
        (op.combinar("9", "inner", ["id"], ["WORK.a", "WORK.b"]), "join"),
        (op.agregar("10", ["ciudad"], [{"expression": "sum(x)", "alias": "t"}]), "aggregate"),
        (op.ordenar("11", ["id"]), "sort"),
        (op.deduplicar("12", ["id"]), "dedup"),
        (op.concatenar("13", ["WORK.a", "WORK.b"]), "union"),
        (op.pivotar("14", ["id"], "mes"), "pivot"),
        (op.iterar("15", "plantilla", [{"prefijo": "a"}]), "iterate"),
        (op.controlar("16", "by_group"), "stateful_row"),
    ]
    for operador, kind in casos:
        assert operador.kind == kind
        assert kind in OPERATOR_KINDS
        assert operador.signature == signature(kind, operador.params)
        assert len(operador.signature) == 16


def test_el_grafo_acepta_los_operadores_construidos():
    grafo = Graph()
    for operador in [op.leer("1", "WORK.a"), op.pivotar("2", ["id"], "mes")]:
        grafo.add_operator(operador)
    assert len(grafo) == 2


def test_pivotar_queda_como_hueco():
    assert op.pivotar("1", ["id"], "mes").status == "hueco"


def test_los_nombres_se_normalizan_a_minusculas():
    operador = op.proyectar("1", "drop", ["Saldo", "ID"])
    assert operador.params["names"] == ["saldo", "id"]


@pytest.mark.parametrize(
    "construir, error",
    [
        (lambda: op.leer("1", "  "), "dataset"),
        (lambda: op.leer_archivo("1", "x.csv", []), "outputs"),
        (lambda: op.filtrar("1", ""), "expression"),
        (lambda: op.proyectar("1", "rename", ["a"]), "mode"),
        (lambda: op.proyectar("1", "keep", []), "names"),
        (lambda: op.renombrar("1", []), "al menos un par"),
        (lambda: op.renombrar("1", [("a",)]), "origen y destino"),
        (lambda: op.calcular("1", []), "asignación"),
        (lambda: op.unir("1", "outer", [("a.id", "b.id")], ["a", "b"]), "join_type"),
        (lambda: op.unir("1", "inner", [], ["a", "b"]), "llave"),
        (lambda: op.unir("1", "inner", [("a.id", "b.id")], "a"), "debe ser una lista"),
        (lambda: op.combinar("1", "outer", ["id"], ["a", "b"]), "join_type"),
        (lambda: op.agregar("1", ["g"], []), "agregado"),
        (lambda: op.ordenar("1", []), "by"),
        (lambda: op.deduplicar("1", ["id"], keep="middle"), "keep"),
        (lambda: op.concatenar("1", ["solo"]), "al menos 2"),
        (lambda: op.iterar("1", "p", []), "instancia"),
        (lambda: op.controlar("1", ""), "reason"),
    ],
)
def test_parametros_invalidos_se_rechazan(construir, error):
    with pytest.raises(ValueError, match=error):
        construir()


def test_unir_tiene_la_forma_del_lowering_de_sql():
    operador = op.unir("1", "left", [("t.id", "h.cname")], ["WORK.t", "WORK.h"], "x > 0")
    assert operador.params == {
        "by": ["id"],
        "keys": [["t.id", "h.cname"]],
        "join_type": "left",
        "sources": ["WORK.t", "WORK.h"],
        "condition": "x > 0",
    }


def test_cross_no_necesita_llave():
    assert op.unir("1", "cross", [], ["WORK.a", "WORK.b"]).params["join_type"] == "cross"


def test_combinar_no_tiene_keys_como_el_merge_del_lowering():
    operador = op.combinar("1", "inner", ["id"], ["WORK.a", "WORK.b"])
    assert set(operador.params) == {"by", "join_type", "sources"}


def test_calcular_conserva_claves_extra_y_los_opcionales_del_lowering():
    operador = op.calcular(
        "1",
        [{"target": "x", "expression": "y + 1", "origin": "columna"}],
        outputs=["WORK.t"],
        modo="agrega",
        declared={"x": ["Double", None]},
    )
    assert operador.params["assignments"] == [
        {"target": "x", "expression": "y + 1", "origin": "columna"}
    ]
    assert operador.params["modo"] == "agrega"
    assert operador.params["declared"] == {"x": ["Double", None]}


def test_agregar_con_columnas_pendientes_queda_parcial():
    operador = op.agregar(
        "1", ["ciudad"], [{"expression": "SUM(x)", "alias": "t"}],
        pendiente=["nombre"], status="parcial",
    )
    assert operador.status == "parcial"
    assert operador.params["pendiente"] == ["nombre"]


def test_leer_tiene_dos_formas_como_el_lowering():
    assert op.leer("1", "WORK.a").params == {"dataset": "WORK.a"}
    assert op.leer("1", "WORK.a", incluir_bandera=True).params == {"dataset": "WORK.a", "in": None}
    assert op.leer("1", "WORK.a", "ea").params == {"dataset": "WORK.a", "in": "ea"}


def test_escribir_archivo_y_leer_archivo_llevan_todas_sus_opciones():
    lectura = op.leer_archivo("1", "x.csv", ["WORK.a"])
    assert set(lectura.params) == {
        "datafile", "outputs", "dbms", "delimiter", "getnames", "sheet", "guessingrows",
    }
    escritura = op.escribir_archivo("2", ["WORK.a"], "s.csv", dbms="csv")
    assert escritura.kind == "write_file"
    assert escritura.params["dbms"] == "csv"
