"""Pruebas de las herramientas de `tools/referencia/` y de que la documentación descargada está completa.

Las funciones que hacen red no se prueban aquí; sus partes puras (enlaces, índices, URLs) sí.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "referencia"))

import descargar  # noqa: E402
import fuentes  # noqa: E402
import indice  # noqa: E402


@dataclass
class _Marcador:
    title: str


def test_subpaginas_se_buscan_por_nombre_no_por_carpeta():
    base = "https://help.qlik.com/talend/en-US/components/8.0/tjdbcinput"
    md = (
        "[tJDBCInput Standard properties]"
        "(https://help.qlik.com/talend/en-US/components/8.0/jdbc/tjdbcinput-standard-properties)\n"
        "[otro componente](https://help.qlik.com/talend/en-US/components/8.0/tsqltemplate)\n"
        "[a sí misma](https://help.qlik.com/talend/en-US/components/8.0/tjdbcinput)\n"
    )
    assert descargar.enlaces_de_subpaginas(md, base) == [
        "https://help.qlik.com/talend/en-US/components/8.0/jdbc/tjdbcinput-standard-properties"
    ]


def test_enlaces_repetidos_se_cuentan_una_vez():
    base = "https://help.qlik.com/talend/en-US/components/8.0/tmap"
    enlace = "[tMap](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap)"
    assert descargar.enlaces_de_subpaginas(enlace + "\n" + enlace, base) == [
        "https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap"
    ]


def test_aplanar_marcadores_respeta_el_orden_y_el_nivel():
    marcadores = [
        _Marcador("Prefacio"),
        [_Marcador("Sintaxis"), [_Marcador("Caracteres especiales")]],
        _Marcador("PROC SQL"),
    ]
    paginas = {"Prefacio": 3, "Sintaxis": 7, "Caracteres especiales": 10, "PROC SQL": 13}
    filas = indice.aplanar(marcadores, lambda m: paginas[m.title])
    assert filas == [
        (0, "Prefacio", 3),
        (1, "Sintaxis", 7),
        (2, "Caracteres especiales", 10),
        (0, "PROC SQL", 13),
    ]


def test_markdown_del_indice_sangra_por_nivel():
    texto = indice.markdown_indice("Guía", "guia.txt", [(0, "A", 1), (1, "B", None)])
    assert "- A (p. 1)" in texto
    assert "  - B (p. ?)" in texto
    assert "busca `<!-- página N -->`" in texto


def test_urls_de_las_fuentes():
    assert fuentes.url_sas("proc").endswith("/docsets/proc/content/proc.pdf?locale=en")
    assert fuentes.url_componente("TMap") == fuentes.TALEND_BASE + "tmap"
    assert fuentes.url_studio("defining-variables").endswith("/defining-variables")


def test_cada_guia_sas_tiene_texto_e_indice_en_docs():
    # Los PDF no se versionan (ver .gitignore): se regeneran con descargar.py. Lo que sí se
    # versiona, el texto y el índice, debe estar para cada guía.
    carpeta = REPO / "docs" / "referencia" / "sas"
    for guia in fuentes.SAS_DOCSETS:
        assert (carpeta / f"{guia.archivo}.txt").exists(), guia.archivo
        assert (carpeta / f"{guia.archivo}.INDEX.md").exists(), guia.archivo


def test_cada_componente_talend_del_proyecto_tiene_su_pagina():
    carpeta = REPO / "docs" / "referencia" / "talend"
    faltantes = [c for c in fuentes.TALEND_COMPONENTES if not (carpeta / f"{c}.md").exists()]
    assert faltantes == []
