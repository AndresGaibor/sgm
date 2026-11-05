"""Escáner de secretos: valores limpios que no deben dar hallazgo, y la lista blanca auditable.

Incluye la regla de oro: el emisor `sgm talend` sobre client_large no produce hallazgos, y las
carpetas `decisiones/` y `tests/fixtures/sas/client/` tampoco.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import sgm.seguridad.reglas_xml as reglas_xml
from sgm.cli import app
from sgm.seguridad.escaner_secretos import escanear_ruta, escanear_texto
from sgm.seguridad.lista_blanca import LISTA_BLANCA

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"

LIMPIOS = [
    "password=***;",
    "pwd=&pwd_macro.;",
    "password=context.db_pass;",
    "pwd='';",
    'pwd="";',
    "password_policy = strong;",
    "proc pwencode in='***';",
    "https://svc:***@host.example/api",
    "https://host.example/api",
    "Authorization: Bearer <token>",
    '<contextParameter name="DB_PASS" type="id_Password" value=""/>',
    '<contextParameter name="DB_PASS" type="id_Password" value="***"/>',
    '<elementParameter field="PASSWORD" name="PASS" value="" show="false"/>',
    '<elementParameter field="PASSWORD" name="PASSWORD" value="***"/>',
    "proc pwencode in=&clave_macro;",
    "proc pwencode in=`...`;",
    "TOKEN_URL = 'https://ejemplo.invalido/ruta';",
    "titulo = 'Contraseña de ejemplo: ver docs';",
]


@pytest.mark.parametrize("texto", LIMPIOS)
def test_valores_limpios_no_dan_hallazgo(texto: str) -> None:
    assert escanear_texto(texto) == []


def test_sgm_ref_de_tfileinputexcel_no_da_hallazgo() -> None:
    texto = (
        '<node componentName="tFileInputExcel" componentVersion="0.102">\n'
        '  <elementParameter field="PASSWORD" name="PASSWORD" value="&quot;sgm_ref&quot;"/>\n'
        "</node>\n"
    )
    assert escanear_texto(texto) == []


def test_sgm_ref_en_otro_componente_si_da_hallazgo() -> None:
    """La lista blanca es por componente: el mismo valor en un tJava no está permitido."""
    texto = (
        '<node componentName="tJava" componentVersion="0.102">\n'
        '  <elementParameter field="PASSWORD" name="PASSWORD" value="&quot;sgm_ref&quot;"/>\n'
        "</node>\n"
    )
    (hallazgo,) = escanear_texto(texto)
    assert hallazgo.tipo == "password_en_item"
    assert hallazgo.linea == 2


def test_la_lista_blanca_tiene_motivo_y_se_puede_auditar() -> None:
    assert LISTA_BLANCA
    for entrada in LISTA_BLANCA:
        assert entrada.motivo.strip(), entrada
        assert entrada.campo and entrada.componente and entrada.valor


def test_la_lista_blanca_es_la_unica_razon_del_silencio(emitidos: Path, monkeypatch) -> None:
    """Sin la lista blanca, los `sgm_ref` del emisor sí aparecen: el silencio es por la lista."""
    monkeypatch.setattr(reglas_xml, "permitido", lambda *_: False)
    hallazgos = escanear_ruta(emitidos).hallazgos
    assert hallazgos, "el emisor debe emitir al menos un PASSWORD con sgm_ref"
    assert {h.tipo for h in hallazgos} == {"password_en_item"}
    assert all(h.valor == '"s***' for h in hallazgos)


@pytest.fixture(scope="module")
def emitidos(tmp_path_factory) -> Path:
    """Artefactos reales de `sgm talend` sobre client_large, emitidos por el mismo comando."""
    destino = tmp_path_factory.mktemp("secretos_emision")
    resultado = CliRunner().invoke(app, ["talend", str(FUENTE), "--out", str(destino)])
    assert resultado.exit_code == 0, resultado.output
    return destino / "client_large"


def test_el_emisor_sobre_client_large_no_produce_hallazgos(emitidos: Path) -> None:
    escaneo = escanear_ruta(emitidos)
    assert escaneo.revisados >= 8, "se esperan los 4 .item y los 4 .properties"
    assert escaneo.hallazgos == (), [(h.archivo, h.linea, h.tipo) for h in escaneo.hallazgos]


def test_el_emisor_sobre_client_large_pasa_el_cli(emitidos: Path) -> None:
    resultado = CliRunner().invoke(app, ["secretos", str(emitidos)])
    assert resultado.exit_code == 0, resultado.output


def test_decisiones_no_tiene_contrasenas_en_claro() -> None:
    escaneo = escanear_ruta(RAIZ / "decisiones")
    assert escaneo.revisados >= 4
    assert escaneo.hallazgos == ()


def test_los_sas_del_cliente_no_tienen_contrasenas_en_claro() -> None:
    escaneo = escanear_ruta(RAIZ / "tests" / "fixtures" / "sas" / "client")
    assert escaneo.revisados >= 2
    assert escaneo.hallazgos == ()
