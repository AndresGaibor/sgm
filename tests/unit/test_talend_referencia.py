"""Pruebas de la documentación de Talend: catálogo completo, verificación contra el catálogo,
huella del inventario y extracto de opciones.

Si el inventario cambia, la prueba de huella falla a propósito: revisar qué cambió y actualizar
`docs/referencia/talend/inventario.sha256`.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "referencia"))

import opciones  # noqa: E402
import verificar  # noqa: E402

CATALOGO = REPO / "rules" / "talend" / "components.json"
PAGINAS = REPO / "docs" / "referencia" / "talend" / "catalogo"


def _nombres() -> list[str]:
    return list(json.loads(CATALOGO.read_text(encoding="utf-8"))["components"])


def test_cada_componente_del_catalogo_tiene_su_pagina():
    faltan = [n for n in _nombres() if not (PAGINAS / f"{n.lower()}.md").exists()]
    assert faltan == []


def test_la_verificacion_no_tiene_titulos_ni_paginas_faltantes():
    resultados = verificar.verificar_catalogo(CATALOGO, PAGINAS)
    graves = [p for r in resultados for p in r.problemas if "título" in p or "falta" in p]
    assert graves == []


def test_el_informe_de_verificacion_esta_al_dia():
    resultados = verificar.verificar_catalogo(CATALOGO, PAGINAS)
    informe = (PAGINAS / "VERIFICACION.md").read_text(encoding="utf-8")
    assert informe == verificar.markdown_informe(resultados), (
        "VERIFICACION.md no coincide con el catálogo: ejecuta tools/referencia/verificar.py"
    )


def test_normalizar_familia_iguala_logs_and_errors_con_logs_errors():
    assert verificar.normalizar_familia("Logs & Errors") == verificar.normalizar_familia(
        "Logs_Errors"
    )


def test_una_familia_distinta_se_marca_como_problema():
    pagina = "# tX\n\nThe Standard tX component belongs to the ESB family.\n"
    res = verificar.verificar_pagina("tX", ["Internet"], pagina)
    assert res.problemas and "ESB" in res.problemas[0]


def test_el_titulo_que_no_coincide_se_marca():
    res = verificar.verificar_pagina("tX", ["Processing"], "# tY\n")
    assert any("título" in p for p in res.problemas)


def test_la_huella_del_inventario_no_cambio_sin_revisarse():
    inventario = REPO / "rules" / "talend" / "official-component-inventory.json"
    huella = hashlib.sha256(inventario.read_bytes()).hexdigest()
    registrada = yaml.safe_load(
        (REPO / "docs" / "referencia" / "talend" / "inventario.sha256").read_text(encoding="utf-8")
    )
    assert huella == registrada["sha256"], (
        "el inventario de Talend cambió: revisa qué cambió y actualiza inventario.sha256"
    )


def test_las_opciones_de_tjdbcconnection_se_extraen():
    datos = yaml.safe_load(
        (REPO / "docs" / "referencia" / "talend" / "tjdbcconnection-opciones.yaml").read_text(
            encoding="utf-8"
        )
    )
    secciones = {s["seccion"]: s["propiedades"] for s in datos["secciones"]}
    assert "Basic settings" in secciones
    nombres = {p["propiedad"] for p in secciones["Basic settings"]}
    assert {"JDBC URL", "Driver Class", "Drivers"} <= nombres


def test_limpiar_quita_html_y_entidades():
    assert opciones.limpiar("Hola<br>mundo &gt; <span>x</span>") == "Hola mundo > x"


def test_opciones_por_seccion_lee_solo_las_tablas_de_propiedades():
    md = (
        "## Basic settings\n\n| Properties | Description |\n| --- | --- |\n"
        "| JDBC URL | La URL. |\n\n## Usage\n\nTexto sin tabla.\n"
    )
    assert opciones.opciones_por_seccion(md) == {
        "Basic settings": [{"propiedad": "JDBC URL", "descripcion": "La URL."}]
    }
