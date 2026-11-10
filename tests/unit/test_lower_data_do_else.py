"""Casos admitidos y rechazados al bajar bloques IF/THEN DO/ELSE."""

from sgm.frontend.datastep import classify_statement
from sgm.ir.lower_data_statements import conditional_do_assignments


def _sentencias(*textos: str):
    return [classify_statement(texto, indice + 1) for indice, texto in enumerate(textos)]


def test_if_then_do_else_conserva_valor_de_destino_sin_asignacion_en_else():
    statements = _sentencias(
        "if saldo < 0 then do",
        "revision = 'SI'",
        "saldo = 0",
        "end",
        "else revision = 'NO'",
    )

    result = conditional_do_assignments(statements, 0)

    assert result == (
        [
            {
                "target": "revision",
                "expression": "'SI'",
                "conditional": {"condition": "saldo < 0", "otherwise": "'NO'"},
            },
            {
                "target": "saldo",
                "expression": "0",
                "conditional": {"condition": "saldo < 0", "otherwise": "saldo"},
            },
        ],
        5,
    )


def test_if_then_do_else_rechaza_sentencias_que_no_sean_asignaciones_simples():
    statements = _sentencias(
        "if saldo < 0 then do",
        "revision = 'SI'",
        "output",
        "end",
        "else revision = 'NO'",
    )

    assert conditional_do_assignments(statements, 0) is None


def test_if_then_do_else_rechaza_destinos_duplicados_en_el_bloque():
    statements = _sentencias(
        "if saldo < 0 then do",
        "revision = 'SI'",
        "revision = 'OK'",
        "end",
        "else revision = 'NO'",
    )

    assert conditional_do_assignments(statements, 0) is None


def test_if_then_do_else_rechaza_cambiar_condicion_antes_de_terminar_el_bloque():
    statements = _sentencias(
        "if saldo < 0 then do",
        "saldo = 0",
        "revision = 'SI'",
        "end",
        "else revision = 'NO'",
    )

    assert conditional_do_assignments(statements, 0) is None


def test_if_then_do_else_rechaza_condicion_vacia():
    statements = _sentencias(
        "if then do",
        "revision = 'SI'",
        "end",
        "else revision = 'NO'",
    )

    assert conditional_do_assignments(statements, 0) is None
