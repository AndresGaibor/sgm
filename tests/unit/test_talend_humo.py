"""Prueba de humo de los Jobs que emite `sgm talend`, sin abrir Talend Studio.

Recorre los cuatro Jobs del programa y comprueba los errores que ya aparecieron en los hitos
59 a 66: conexiones desactivadas, `tRunJob` a un Job inexistente, conexiones a nodos que no
existen, `UNIQUE_NAME` repetidos, contraseñas en claro, variables de contexto usadas sin
declarar y XML mal formado. Es la red que evita repetirlos.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.cli import app

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"


@pytest.fixture(scope="module")
def jobs(tmp_path_factory) -> dict[str, ET.Element]:
    """Emite los Jobs del programa una vez y devuelve cada `.item` ya parseado por nombre."""
    destino = tmp_path_factory.mktemp("humo")
    resultado = CliRunner().invoke(app, ["talend", str(FUENTE), "--out", str(destino)])
    assert resultado.exit_code == 0, resultado.output
    carpeta = destino / "client_large" / "talend" / "process"
    emitidos = {}
    for archivo in sorted(carpeta.glob("*.item")):
        nombre = re.sub(r"_\d+\.\d+\.item$", "", archivo.name)
        emitidos[nombre] = ET.parse(archivo).getroot()
    assert set(emitidos) == {
        "job_exogena_depositos",
        "job_producto",
        "job_totales",
        "job_conciliacion",
    }
    return emitidos


def _parametro(nodo: ET.Element, nombre: str) -> str | None:
    encontrado = nodo.find(f"elementParameter[@name='{nombre}']")
    return None if encontrado is None else encontrado.get("value")


def _nombres_de_nodo(raiz: ET.Element) -> list[str]:
    """Solo los `UNIQUE_NAME` de los nodos: las conexiones y el `<subjob>` repiten el nombre."""
    return [
        p.get("value", "")
        for nodo in raiz.findall("node")
        for p in nodo.findall("elementParameter")
        if p.get("name") == "UNIQUE_NAME"
    ]


def _contexto(raiz: ET.Element) -> set[str]:
    return {c.get("name", "") for c in raiz.iter("contextParameter")}


def _codigo(nodo: ET.Element) -> str:
    return "\n".join(
        p.get("value", "")
        for p in nodo.findall("elementParameter")
        if p.get("name") in {"CODE", "EXPRESSION", "CONDITION", "FILENAME", "LABEL", "PROCESS"}
    )


def test_ninguna_conexion_queda_desactivada(jobs):
    for nombre, raiz in jobs.items():
        desactivadas = [
            p.get("value")
            for p in raiz.iter("elementParameter")
            if p.get("name") == "ACTIVATE" and p.get("value") == "false"
        ]
        assert desactivadas == [], f"{nombre}: conexiones con ACTIVATE=false"


def test_todo_trunjob_apunta_a_un_job_emitido(jobs):
    nombres = set(jobs)
    for nombre, raiz in jobs.items():
        for nodo in raiz.iter("node"):
            if nodo.get("componentName") != "tRunJob":
                continue
            destino = _parametro(nodo, "PROCESS")
            assert destino in nombres, f"{nombre}: tRunJob apunta a {destino!r}, que no existe"


def test_cada_conexion_referencia_nodos_existentes(jobs):
    for nombre, raiz in jobs.items():
        nodos = set(_nombres_de_nodo(raiz))
        for conexion in raiz.iter("connection"):
            assert conexion.get("source") in nodos, f"{nombre}: origen inexistente"
            assert conexion.get("target") in nodos, f"{nombre}: destino inexistente"


def test_los_unique_name_son_unicos_dentro_de_cada_job(jobs):
    for nombre, raiz in jobs.items():
        nodos = _nombres_de_nodo(raiz)
        repetidos = sorted({n for n in nodos if nodos.count(n) > 1})
        assert repetidos == [], f"{nombre}: UNIQUE_NAME repetidos {repetidos}"


def test_ningun_password_va_en_claro(jobs):
    """Valores aceptados: vacío, la máscara `***` y el marcador `sgm_ref` que evita el fallo de
    compilación de `tFileInputExcel`. Cualquier otro sería un secreto dentro del repositorio."""
    permitidos = {"", "***", "''", '""', '"sgm_ref"'}
    for nombre, raiz in jobs.items():
        for parametro in raiz.iter("elementParameter"):
            if parametro.get("name") != "PASSWORD":
                continue
            valor = (parametro.get("value") or "").strip()
            assert valor in permitidos, f"{nombre}: PASSWORD con valor en claro"


def test_toda_variable_de_contexto_usada_esta_declarada(jobs):
    for nombre, raiz in jobs.items():
        declaradas = _contexto(raiz)
        usadas: set[str] = set()
        for nodo in raiz.iter("node"):
            usadas.update(re.findall(r"context\.([A-Za-z_][A-Za-z0-9_]*)", _codigo(nodo)))
        faltan = sorted(usadas - declaradas)
        assert faltan == [], f"{nombre}: usa variables sin declarar {faltan}"


def test_los_item_son_xml_bien_formado(jobs):
    for nombre, raiz in jobs.items():
        assert raiz.tag.endswith("ProcessType"), f"{nombre}: raíz inesperada {raiz.tag!r}"
        assert raiz.findall("node"), f"{nombre}: el Job no tiene nodos"
