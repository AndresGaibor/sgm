"""Fase 2 de `docs/automatizacion/03-plan-produccion.md`: conflictos entre reglas.

Dos reglas de igual prioridad que proponen componentes distintos no se resuelven en silencio:
el resolutor reporta el conflicto. Mayor prioridad gana sin conflicto.
"""

from __future__ import annotations

from sgm.ir.models import Operator
from sgm.passes.p10_components import Rule, resolve

MOTORES: dict[str, dict[str, str]] = {}


def _regla(id_: str, prioridad: int, componente: str, kind: str = "filter") -> Rule:
    return Rule(
        id=id_,
        version=1,
        prioridad=prioridad,
        cuando={"kind": kind},
        produce={"component": componente},
        confidence="alta",
        alternatives=(),
    )


def _op() -> Operator:
    return Operator(id="op_1", kind="filter", placement="flow")


def test_mismo_peldano_con_componentes_distintos_es_conflicto() -> None:
    reglas = [_regla("a", 80, "tFilterRow"), _regla("b", 80, "tMap")]
    elegido, conflicto = resolve(_op(), reglas, MOTORES)
    assert conflicto is not None
    assert {comp for _, comp in conflicto.opciones} == {"tFilterRow", "tMap"}
    assert elegido is not None


def test_mayor_prioridad_gana_sin_conflicto() -> None:
    reglas = [_regla("a", 80, "tFilterRow"), _regla("b", 50, "tMap")]
    elegido, conflicto = resolve(_op(), reglas, MOTORES)
    assert conflicto is None
    assert elegido is not None and elegido[1] == "tFilterRow"


def test_mismo_componente_no_es_conflicto() -> None:
    reglas = [_regla("a", 80, "tFilterRow"), _regla("b", 80, "tFilterRow")]
    _, conflicto = resolve(_op(), reglas, MOTORES)
    assert conflicto is None


def test_sin_regla_que_aplique() -> None:
    reglas = [_regla("a", 80, "tMap", kind="join")]
    assert resolve(_op(), reglas, MOTORES) == (None, None)


def test_condicion_fuera_del_lenguaje_se_rechaza() -> None:
    from pathlib import Path

    import jsonschema

    from sgm import rules_validate

    raiz = Path(__file__).resolve().parents[2]
    esquema = rules_validate._schema("mapping", raiz)
    base = {
        "id": "02-demo",
        "version": 1,
        "prioridad": 80,
        "cuando": {"kind": "filter"},
        "produce": {"component": "tFilterRow"},
        "confidence": "alta",
        "alternatives": [],
        "casos": ["tests/cases/02-demo"],
    }
    jsonschema.Draft202012Validator(esquema).validate(base)
    malo = {**base, "cuando": {"kind": "filter", "texto_sas": "x"}}
    errores = list(jsonschema.Draft202012Validator(esquema).iter_errors(malo))
    assert errores
