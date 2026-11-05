"""Pruebas de los casos L8 de validaciones: regeneración reproducible y conteos del generador.

El generador `tools/corpus_datos/validaciones.py` escribe las entradas con semilla fija. Estas
pruebas comprueban tres cosas: que regenerar en una carpeta temporal da los mismos bytes que las
entradas guardadas, que los conteos de `caso.yaml` son los que plantó el generador, y que el
orden de columnas de los CSV coincide con el que deduce `origenes_producto` del programa original.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import zipfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "tests" / "corpus" / "L8" / "validaciones"
GENERADOR = REPO / "tools" / "corpus_datos" / "validaciones.py"
ORIGINAL = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"


def _modulo():
    spec = importlib.util.spec_from_file_location("validaciones_gen", GENERADOR)
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _caso_yaml(caso: str) -> dict:
    return yaml.safe_load((CORPUS / caso / "caso.yaml").read_text(encoding="utf-8"))


def _hoja_xlsx(ruta: Path) -> str:
    """Contenido XML de la hoja: determinista, a diferencia de los metadatos del zip."""
    with zipfile.ZipFile(ruta) as paquete:
        return paquete.read("xl/worksheets/sheet1.xml").decode("utf-8")


def test_regenerar_da_los_mismos_bytes(tmp_path: Path) -> None:
    gen = _modulo()
    gen.generar_todo(tmp_path)
    for caso in gen.CASOS:
        guardadas = sorted((CORPUS / caso / "entradas").iterdir())
        regeneradas = sorted((tmp_path / caso / "entradas").iterdir())
        assert [p.name for p in guardadas] == [p.name for p in regeneradas], caso
        for guardada, nueva in zip(guardadas, regeneradas, strict=True):
            if guardada.suffix == ".xlsx":
                assert _hoja_xlsx(guardada) == _hoja_xlsx(nueva), f"{caso}/{guardada.name}"
            else:
                assert guardada.read_bytes() == nueva.read_bytes(), f"{caso}/{guardada.name}"


def test_conteos_de_caso_yaml_coinciden_con_el_generador() -> None:
    gen = _modulo()
    for caso in gen.CASOS:
        esperado = gen.conteos_caso(caso)
        guardado = _caso_yaml(caso)["anomalias_plantadas"]
        assert guardado == esperado, caso


def test_cada_fila_anomala_cuenta_una_sola_vez() -> None:
    """Un conteo por tipo y producto: la suma de conteos es el total de filas del CSV."""
    gen = _modulo()
    for caso in gen.CASOS:
        spec = gen.CASOS[caso]
        for nombre, conteo in spec.get("productos", {}).items():
            filas = (CORPUS / caso / "entradas" / gen.PRODUCTOS[nombre].archivo).read_text(
                encoding="utf-8"
            )
            assert len(filas.splitlines()) == sum(conteo.values()), (caso, nombre)


def test_orden_de_columnas_coincide_con_origenes_producto() -> None:
    sys.path.insert(0, str(GENERADOR.parent))
    from validaciones_filas import NOMBRES_23

    from sgm.proceso.origen_producto import origenes_producto

    texto = ORIGINAL.read_text(encoding="utf-8", errors="replace")
    origenes = origenes_producto(
        texto, {"cte": ("CTE", "CORRIENTE"), "aho": ("AHO", "AHORROS"), "nequi": ("NEQUI",)}
    )
    assert origenes.columnas_comunes == NOMBRES_23


def test_programas_entre_120_y_300_lineas_con_etiquetas() -> None:
    for carpeta in sorted(CORPUS.iterdir()):
        if not carpeta.is_dir():
            continue
        texto = (carpeta / "programa.sas").read_text(encoding="utf-8")
        lineas = texto.count("\n")
        assert 120 <= lineas <= 300, f"{carpeta.name}: {lineas} líneas"
        assert len(re.findall(r"/\* Etiqueta:", texto)) >= 5, carpeta.name
