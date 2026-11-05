"""Pruebas de los casos L8 de validaciones: entradas, esperado por construcción y cruce.

El generador `tools/corpus_datos/validaciones.py` escribe las entradas con semilla fija y el
`esperado/` a partir de la verdad plantada. Estas pruebas comprueban que regenerar da los mismos
bytes, que los conteos de `caso.yaml` son los que plantó el generador, que las salidas del yaml
son las que produce el esperado, que las invariantes se cumplen y que el cruce con el oráculo SQL
no tiene diferencias en lo que verifica.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "tests" / "corpus" / "L8" / "validaciones"
GENERADOR = REPO / "tools" / "corpus_datos" / "validaciones.py"
ORIGINAL = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
for _ruta in (REPO / "tools", REPO / "tools" / "corpus_datos"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

from corpus_lib.caso import ESTADOS  # noqa: E402
from corpus_lib.invariantes import analizar, comprobar  # noqa: E402


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


def _archivos(carpeta: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(carpeta)).replace("\\", "/"): p.read_bytes()
        for p in sorted(carpeta.rglob("*"))
        if p.is_file()
    }


def _filas(ruta: Path) -> int:
    """Filas de datos de un CSV con cabecera."""
    lineas = [ln for ln in ruta.read_text(encoding="utf-8").splitlines() if ln]
    return len(lineas) - 1


def _casos() -> list[str]:
    return sorted(p.name for p in CORPUS.iterdir() if (p / "caso.yaml").is_file())


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


def test_esperado_se_regenera_igual(tmp_path: Path) -> None:
    """Regenerar `esperado/` en una carpeta temporal da exactamente lo guardado."""
    gen = _modulo()
    gen.generar_todo(tmp_path)
    for caso in gen.CASOS:
        guardado = _archivos(CORPUS / caso / "esperado")
        regenerado = _archivos(tmp_path / caso / "esperado")
        assert guardado.keys() == regenerado.keys(), caso
        for nombre in guardado:
            assert guardado[nombre] == regenerado[nombre], f"{caso}/esperado/{nombre}"


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
    for carpeta in _casos():
        texto = (CORPUS / carpeta / "programa.sas").read_text(encoding="utf-8")
        lineas = texto.count("\n")
        assert 120 <= lineas <= 300, f"{carpeta}: {lineas} líneas"
        assert len(re.findall(r"/\* Etiqueta:", texto)) >= 5, carpeta


@pytest.mark.parametrize("caso", _casos())
def test_salidas_del_yaml_son_las_del_esperado(caso: str) -> None:
    """Las tablas WORK y los archivos del yaml son exactamente los que escribe el esperado."""
    salidas = _caso_yaml(caso)["salidas_esperadas"]
    tablas = {p.stem for p in (CORPUS / caso / "esperado").glob("*.csv")}
    archivos = {p.name for p in (CORPUS / caso / "esperado" / "archivos").glob("*.csv")}
    assert tablas == set(salidas["tablas_work"]), caso
    assert archivos == set(salidas["archivos"]), caso


CASOS_CON_RECHAZO = [c for c in _casos() if not c.startswith("v06")]
MOTIVO_POR_LABEL = {
    "nombre_con_espacios": "ESPACIOS EN NOMBRE",
    "nombre_con_enie": "NOMBRE CON ENIE",
    "nombre_con_tildes": "NOMBRE CON TILDES",
    "nombre_minusculas": "NOMBRE EN MINUSCULAS",
    "valor_con_espacios": "VALOR CON ESPACIOS",
    "validos": "SIN CAMBIO",
}


@pytest.mark.parametrize("caso", CASOS_CON_RECHAZO)
def test_conteos_del_esperado_igualan_anomalias(caso: str) -> None:
    """Rechazados y válidos del esperado suman las filas de la sabana, y cuadran con el yaml.

    Una fila planteada como `tipo_cta_invalido_no_validado` (v08) no la rechaza el programa: cuenta
    como válida. Ese caso está escrito en el yaml, no inferido.
    """
    esp = CORPUS / caso / "esperado"
    anomalias = _caso_yaml(caso)["anomalias_plantadas"]
    for producto, conteo in anomalias.items():
        p = producto.upper()
        total = sum(conteo.values())
        if caso.startswith("v03"):
            origen = _filas(esp / f"SABANA_UBIC_{p}.csv")
            rechazos = _filas(esp / f"INCONS_UBICACION_{p}.csv")
            validos = _filas(esp / f"UBIC_VALIDA_{p}.csv")
        else:
            origen = _filas(esp / f"SABANA_{p}.csv")
            rechazos, validos = _rechazos_validos(caso, p, esp)
        assert origen == total, (caso, p)
        assert rechazos + validos == origen, (caso, p)
        falsos_validos = conteo.get("tipo_cta_invalido_no_validado", 0)
        assert validos == conteo["validos"] + falsos_validos, (caso, p)
        assert rechazos == total - conteo["validos"] - falsos_validos, (caso, p)


def test_v06_conteo_por_motivo_igual_a_las_etiquetas() -> None:
    """v06 no rechaza filas: cada motivo del esperado cuenta lo que plantó su etiqueta."""
    anomalias = _caso_yaml("v06_normalizacion")["anomalias_plantadas"]
    esp = CORPUS / "v06_normalizacion" / "esperado"
    for producto, conteo in anomalias.items():
        p = producto.upper()
        obtenido = {}
        for linea in (esp / f"CONTEO_MOTIVO_{p}.csv").read_text(encoding="utf-8").splitlines()[1:]:
            motivo, n = linea.rsplit(",", 1)
            obtenido[motivo] = int(n)
        esperado = {MOTIVO_POR_LABEL[etiqueta]: n for etiqueta, n in conteo.items()}
        assert obtenido == esperado, p
        assert _filas(esp / f"SABANA_NORM_{p}.csv") == sum(conteo.values()), p


def _rechazos_validos(caso: str, p: str, esp: Path) -> tuple[int, int]:
    """Filas rechazadas y válidas de un producto, según el caso, desde las tablas del esperado."""
    if caso.startswith("v01"):
        return _filas(esp / f"RECHAZO_TIPO_DOC_{p}.csv"), _filas(esp / f"TIPO_DOC_VALIDO_{p}.csv")
    if caso.startswith("v02"):
        return _filas(esp / f"RECHAZO_NRO_DOC_{p}.csv"), _filas(
            esp / f"NRO_DOC_NO_VACIO_NI_0_{p}.csv"
        )
    if caso.startswith("v04"):
        return _filas(esp / f"INCONS_CUENTA_{p}.csv"), _filas(esp / f"SABANA_VALIDA_{p}.csv")
    if caso.startswith("v05"):
        rechazos = _filas(esp / f"RECHAZO_CODEX_{p}.csv") + _filas(esp / f"RECHAZO_SALDO_{p}.csv")
        return rechazos, _filas(esp / f"SABANA_VALIDA_{p}.csv")
    if caso.startswith(("v07", "v08")):
        return _filas(esp / f"RECHAZOS_{p}.csv"), _filas(esp / f"SABANA_FINAL_{p}.csv")
    return 0, _filas(esp / f"SABANA_NORM_{p}.csv")  # v06 no rechaza: normaliza


@pytest.mark.parametrize("caso", _casos())
def test_invariantes_se_cumplen(caso: str) -> None:
    datos = _caso_yaml(caso)
    for texto in datos["invariantes"]:
        analizar(texto)
    assert comprobar(datos["invariantes"], [CORPUS / caso / "esperado"], 0) == []


def test_estados_del_yaml_son_validos() -> None:
    for caso in _casos():
        datos = _caso_yaml(caso)
        assert datos["estado"] in ESTADOS, caso
        if datos["estado"] != "traducible":
            assert datos.get("motivo"), caso
        assert datos.get("observacion_revision"), caso


@pytest.mark.parametrize("caso", _casos())
def test_cruce_con_el_oraculo_sin_diferencias(caso: str) -> None:
    """Lo que el oráculo calcula coincide con el esperado. Lo que no calcula, se declara."""
    from validaciones_cruce import cruzar

    informe = cruzar(caso)
    assert informe.diferencias == {}, (caso, informe.diferencias)
    assert informe.verificadas, caso
    # `parcial` si y solo si el oráculo deja tablas sin cruzar (y el motivo lo dice).
    es_parcial = _caso_yaml(caso)["estado"] == "parcial"
    assert bool(informe.no_verificadas) == es_parcial, (caso, informe.no_verificadas)
