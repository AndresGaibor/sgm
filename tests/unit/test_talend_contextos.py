"""Pruebas de los grupos de contexto del `.item`: formato de Studio, orden, ids y escapado."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from sgm.talend_item.item import render_item
from sgm.talend_item.modelo import Job, ParametroContexto

VACIO_DEFAULT = '  <context confirmationNeeded="false" hide="false" name="Default"/>\n  <parameters>'


def _job_con_grupos() -> Job:
    # DEV se inserta primero a propósito: Default debe escribirse igualmente en primer lugar.
    return Job(
        "SGM_REF_Prueba",
        contextos={
            "DEV": [
                ParametroContexto("saludo", valor="hola dev"),
                ParametroContexto("tabla", valor="ventas_dev"),
            ],
            "Default": [
                ParametroContexto("saludo", valor="hola"),
                ParametroContexto("tabla", valor="ventas", pedir=True),
            ],
        },
    )


def _grupos(texto: str) -> list[tuple[str, list[tuple[str, str]]]]:
    raiz = ET.fromstring(texto)
    return [
        (
            ctx.get("name"),
            [(p.get("name"), p.get("value")) for p in ctx.findall("contextParameter")],
        )
        for ctx in raiz.findall("context")
    ]


def test_sin_contextos_el_bloque_default_queda_vacio_como_antes():
    texto = render_item(Job("SGM_REF_Sin"))
    assert VACIO_DEFAULT in texto
    assert texto.count("<context ") == 1


def test_dos_grupos_se_parsean_con_default_primero_y_sus_parametros_en_orden():
    texto = render_item(_job_con_grupos())
    assert _grupos(texto) == [
        ("Default", [("saludo", "hola"), ("tabla", "ventas")]),
        ("DEV", [("saludo", "hola dev"), ("tabla", "ventas_dev")]),
    ]
    assert 'defaultContext="Default"' in texto


def test_cada_parametro_lleva_los_atributos_de_studio_sin_repositorio():
    texto = render_item(_job_con_grupos())
    linea = next(ln for ln in texto.splitlines() if 'name="tabla" prompt' in ln)
    assert re.fullmatch(
        r'    <contextParameter comment="" name="tabla" prompt="tabla\?" '
        r'promptNeeded="true" type="id_String" value="ventas" internalId="_[A-Za-z0-9_-]{22}"/>',
        linea,
    )
    assert "repositoryContextId" not in texto


def test_el_internal_id_es_determinista_y_distinto_por_grupo():
    a = re.findall(r'internalId="([^"]+)"', render_item(_job_con_grupos()))
    b = re.findall(r'internalId="([^"]+)"', render_item(_job_con_grupos()))
    assert a == b
    assert len(a) == len(set(a)) == 4


def test_un_valor_con_comillas_y_saltos_de_linea_se_escapa_y_se_lee_igual():
    valor = 'SELECT "x"\nFROM t\tWHERE a < 1 & b > 2'
    job = Job("SGM_REF_Escape", contextos={"Default": [ParametroContexto("q", valor=valor)]})
    texto = render_item(job)
    assert "\n" not in texto.split('value="', 1)[1].split('"', 1)[0]
    ((_, parametros),) = _grupos(texto)
    assert parametros == [("q", valor)]


def test_un_nombre_repetido_en_un_grupo_es_un_error():
    job = Job(
        "SGM_REF_Dup",
        contextos={"Default": [ParametroContexto("a"), ParametroContexto("a", valor="2")]},
    )
    with pytest.raises(ValueError, match="repite"):
        render_item(job)


def test_un_grupo_sin_parametros_se_escribe_vacio():
    texto = render_item(Job("SGM_REF_Vacio", contextos={"QA": []}))
    assert '<context confirmationNeeded="false" hide="false" name="QA"/>' in texto
    assert _grupos(texto) == [("Default", []), ("QA", [])]
