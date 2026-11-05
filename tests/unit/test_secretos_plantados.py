"""Escáner de secretos: un ejemplo plantado por tipo, y el enmascarado de cada hallazgo.

Los valores son ficticios (`Zx9-ficticio-123`). Ninguna prueba imprime ni compara la salida con el
valor completo: solo se verifica que el valor completo no aparece en ningún hallazgo ni en el CLI.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from sgm.cli import app
from sgm.seguridad.escaner_secretos import escanear_texto

FICTICIO = "Zx9-ficticio-123"

# (tipo esperado, texto plantado). Un caso por cada regla y por cada forma de Talend.
PLANTADOS = [
    ("password_en_cadena", f"libname ora oracle user=svc password={FICTICIO};\n"),
    ("password_en_cadena", f"Driver=X;pwd={FICTICIO};\n"),
    ("password_en_cadena", f"db.password={FICTICIO}\n"),
    ("secreto_en_cadena", f"api_token = {FICTICIO}\n"),
    ("pwencode_en_claro", f"proc pwencode in='{FICTICIO}';\nrun;\n"),
    ("sas_cifrado", 'proxy = "{SAS002}Qz8ficticio77ABC";\n'),
    ("token_bearer", f"Authorization: Bearer {FICTICIO}abc\n"),
    (
        "clave_privada",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEficticio\n-----END RSA PRIVATE KEY-----\n",
    ),
    ("url_con_credenciales", f"https://svc:{FICTICIO}@host.example/api\n"),
    (
        "password_en_item",
        f'<elementParameter field="PASSWORD" name="PASS" value="{FICTICIO}" show="false"/>\n',
    ),
    (
        "password_en_contexto",
        f'<contextParameter name="DB_PASS" type="id_Password" value="{FICTICIO}"/>\n',
    ),
    (
        "password_en_item",
        f'<elementParameter field="ENCRYPTED" name="X" value="{FICTICIO}"/>\n',
    ),
    # El valor de un `.item` va escapado: las comillas llegan como &quot;.
    (
        "password_en_item",
        f'<elementParameter field="PASSWORD" name="PASS" value="&quot;{FICTICIO}&quot;"/>\n',
    ),
]


@pytest.mark.parametrize(("tipo", "texto"), PLANTADOS)
def test_cada_tipo_plantado_se_detecta(tipo: str, texto: str) -> None:
    hallazgos = escanear_texto(texto, "plantado.txt")
    assert [h.tipo for h in hallazgos] == [tipo], texto


@pytest.mark.parametrize(("tipo", "texto"), PLANTADOS)
def test_el_valor_completo_nunca_aparece_en_el_hallazgo(tipo: str, texto: str) -> None:
    hallazgos = escanear_texto(texto, "plantado.txt")
    assert hallazgos
    for h in hallazgos:
        assert FICTICIO not in h.valor
        assert h.valor.endswith("***")


@pytest.mark.parametrize(("tipo", "texto"), PLANTADOS)
def test_el_valor_completo_nunca_sale_por_el_cli(tipo: str, texto: str, tmp_path) -> None:
    archivo = tmp_path / "plantado.item"
    archivo.write_text(texto, encoding="utf-8")
    for formato in ("texto", "json"):
        resultado = CliRunner().invoke(app, ["secretos", str(archivo), "--formato", formato])
        assert resultado.exit_code == 1
        assert FICTICIO not in resultado.output
        assert "Zx9-ficticio" not in resultado.output
        assert "MIIEficticio" not in resultado.output


def test_el_hallazgo_indica_la_linea_correcta() -> None:
    texto = f"uno\ndos\nlibname x oracle password={FICTICIO};\n"
    (hallazgo,) = escanear_texto(texto, "a.sas")
    assert (hallazgo.archivo, hallazgo.linea, hallazgo.tipo) == ("a.sas", 3, "password_en_cadena")


def test_la_salida_json_del_cli_lleva_el_enmascarado(tmp_path) -> None:
    archivo = tmp_path / "x.sas"
    archivo.write_text(f"pwd={FICTICIO};\n", encoding="utf-8")
    resultado = CliRunner().invoke(app, ["secretos", str(archivo), "--formato", "json"])
    datos = json.loads(resultado.output)
    assert datos["hallazgos"] == [
        {"archivo": "x.sas", "linea": 1, "tipo": "password_en_cadena", "valor": "Zx***"}
    ]
