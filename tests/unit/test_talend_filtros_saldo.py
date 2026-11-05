"""Hito 90 / R1-07: el `FIN_SALDO_CTA < 0` como `expressionFilter` nulo-seguro.

Se comprueba la forma de las expresiones Java, el faltante contado como menor que cero, el motivo
que sale del SAS y la cascada de la sábana válida con la cuenta de R1-06.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas_cuenta_real import reglas_cuenta_real
from sgm.proceso.reglas_saldo import INCONSISTENCIA, ReglaSaldo, reglas_saldo
from sgm.talend_item.filtros_saldo import ENTRADA, SALIDAS, negativo, salidas, valido

RAIZ = Path(__file__).resolve().parents[2]
TEXTO_V05 = (
    RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v05_codex_saldos" / "programa.sas"
).read_text(encoding="utf-8", errors="replace")
CLIENTE = (RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas").read_text(
    encoding="utf-8", errors="replace"
)
REGLA, _ = reglas_saldo(TEXTO_V05)
CUENTA, _ = reglas_cuenta_real(CLIENTE)


def test_el_faltante_cuenta_como_negativo_antes_de_parsear():
    expresion = negativo(REGLA)
    assert f"({ENTRADA}.FIN_SALDO_CTA == null" in expresion
    # El faltante se evalúa antes que el `parseDouble` y le cortocircuita.
    assert expresion.index('"".equals(') < expresion.index("parseDouble")
    assert f"java.lang.Double.parseDouble({ENTRADA}.FIN_SALDO_CTA) < 0" in expresion


def test_la_comparacion_de_vacio_usa_el_literal_a_la_izquierda():
    # `"".equals(columna)`, no `columna.equals(...)`: una columna nula no lanza excepción (R1-01).
    expresion = negativo(REGLA)
    assert f'"".equals({ENTRADA}.FIN_SALDO_CTA)' in expresion
    assert f"{ENTRADA}.FIN_SALDO_CTA.equals(" not in expresion


def test_el_umbral_sale_del_sas():
    cambiado = ReglaSaldo(
        REGLA.columna, -1, REGLA.motivo, REGLA.proyeccion_neg, REGLA.proyeccion_valida,
        REGLA.llave, REGLA.productos, REGLA.tablas,
    )  # fmt: skip
    assert "< -1" in negativo(cambiado)


def test_la_sabana_valida_pasa_la_cuenta_y_no_es_negativa():
    expresion = valido(REGLA, CUENTA)
    assert expresion.startswith("(")
    assert f"!{negativo(REGLA)}" in expresion
    # La cuenta válida es el complemento de tipo de cuenta y codex (R1-06).
    assert "!(" in expresion and "RELACION" in expresion


def test_dos_salidas_con_nombres_propios():
    flujos = salidas(REGLA, CUENTA)
    assert [f.nombre for f in flujos] == [SALIDAS["neg"], SALIDAS["valida"]]
    assert SALIDAS["neg"] == "saldo_neg" and SALIDAS["valida"] == "saldo_valida"


def test_el_rechazo_lleva_la_inconsistencia_con_el_motivo_del_sas():
    neg = salidas(REGLA, CUENTA)[0]
    assert [c.nombre for c in neg.columnas] == [*REGLA.proyeccion_neg, INCONSISTENCIA]
    assert neg.expresiones[INCONSISTENCIA] == '"SALDO NEGATIVO"'
    assert neg.filtro == negativo(REGLA)


def test_la_sabana_valida_proyecta_las_nueve_columnas_del_sas():
    valida = salidas(REGLA, CUENTA)[1]
    assert [c.nombre for c in valida.columnas] == list(REGLA.proyeccion_valida)
    assert valida.filtro == valido(REGLA, CUENTA)


def test_sin_proyeccion_no_hay_salidas():
    vacia = ReglaSaldo(
        REGLA.columna, 0, REGLA.motivo, (), (), REGLA.llave, REGLA.productos, REGLA.tablas
    )
    with pytest.raises(ValueError, match="no proyecta"):
        salidas(vacia, CUENTA)
