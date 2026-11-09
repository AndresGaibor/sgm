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
        (op.unir("8", "left", ["id"], ["WORK.a", "WORK.b"]), "join"),
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
        (lambda: op.unir("1", "cross", ["id"], ["a", "b"]), "join_type"),
        (lambda: op.unir("1", "inner", [], ["a", "b"]), "by"),
        (lambda: op.unir("1", "inner", ["id"], ["a"]), "al menos 2"),
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
