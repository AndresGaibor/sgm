"""Regresiones de PROC IMPORT DBMS=XLS/XLSX y del lector OOXML local."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

from sgm.cli_migrar import migrar
from sgm.ir.models import Column, Evidence, Operator, Plan
from sgm.migrar.interprete import NoSoportadoEnInterprete, ejecutar_plan
from sgm.seguridad.escaner_secretos import escanear_ruta
from sgm.talend_item.desde_plan_nodos import nodo_lectura

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.xlsx_minimo import escribir_xlsx  # noqa: E402

from sgm.migrar.lector_xlsx import leer_xlsx  # noqa: E402


def _operador(**params) -> Operator:
    return Operator(
        "op_1",
        "read_file",
        params,
        evidence=[Evidence("programa.sas", 1, 3, None)],
    )


def _valor(nodo, nombre: str) -> str | None:
    return next(
        fila[2]
        for fila in nodo.parametros
        if isinstance(fila, tuple) and fila[1] == nombre
    )


def test_xlsx_determinista_y_lector_respeta_la_hoja(tmp_path):
    hojas = {
        "Datos": [
            ["sku", "unidades", "precio"],
            ["A-1", 2, 10],
            ["B-2", 3, 5],
            ["C-3", 0, 7],
        ],
        "Otra": [["sku", "unidades", "precio"], ["Z-9", 1, 1]],
    }
    primero, segundo = tmp_path / "uno.xlsx", tmp_path / "dos.xlsx"
    escribir_xlsx(primero, hojas)
    escribir_xlsx(segundo, hojas)
    assert primero.read_bytes() == segundo.read_bytes()
    assert leer_xlsx(primero, "Datos") == (
        ["sku", "unidades", "precio"],
        [["A-1", "2", "10"], ["B-2", "3", "5"], ["C-3", "0", "7"]],
    )
    assert leer_xlsx(primero, "Otra")[1] == [["Z-9", "1", "1"]]
    with pytest.raises(KeyError, match="Datos.*Otra"):
        leer_xlsx(primero, "Nada")


def test_lector_xlsx_sin_getnames_usa_nombres_excel_y_conserva_primera_fila(tmp_path):
    libro = tmp_path / "sin_cabecera.xlsx"
    escribir_xlsx(libro, {"Hoja1": [["dato", 2], ["otro", 3]]})

    assert leer_xlsx(libro, getnames=False) == (["A", "B"], [["dato", "2"], ["otro", "3"]])


def test_lector_xlsx_rechaza_relacion_que_sale_del_paquete(tmp_path):
    original = tmp_path / "original.xlsx"
    malicioso = tmp_path / "malicioso.xlsx"
    escribir_xlsx(original, {"Datos": [["id"], [1]]})
    with zipfile.ZipFile(original) as fuente, zipfile.ZipFile(malicioso, "w") as destino:
        for miembro in fuente.namelist():
            datos = fuente.read(miembro)
            if miembro == "xl/_rels/workbook.xml.rels":
                datos = datos.replace(b"worksheets/sheet1.xml", b"../evil.xml")
            destino.writestr(miembro, datos)

    with pytest.raises(ValueError, match="fuera del paquete"):
        leer_xlsx(malicioso)


def test_emisor_excel_usa_marcador_solo_en_xlsx_y_deja_pendiente_tipo_desconocido():
    xlsx = nodo_lectura(
        _operador(dbms="xlsx", datafile="'datos.xlsx'", sheet="Datos", getnames=True),
        [Column("sku"), Column("unidades", "Double", source="derived")],
        "tFileInputExcel_1",
        0,
        0,
    )
    xls = nodo_lectura(
        _operador(dbms="xls", datafile="'datos.xls'", sheet="Datos", getnames=True),
        [Column("sku", "String", source="catalog")],
        "tFileInputExcel_2",
        0,
        0,
    )

    assert _valor(xlsx.nodo, "PASSWORD") == '"sgm_ref"'
    assert _valor(xlsx.nodo, "VERSION_2007") == "true"
    assert [p.codigo for p in xlsx.pendientes] == ["P-TIPO-EXCEL"]
    assert _valor(xls.nodo, "VERSION_2007") == "false"
    assert _valor(xls.nodo, "PASSWORD") == ""
    assert all(p.codigo != "P-HOJA" for p in xlsx.pendientes)


def test_guessingrows_excel_sigue_pendiente():
    resultado = nodo_lectura(
        _operador(
            dbms="xlsx",
            datafile="'datos.xlsx'",
            sheet="Datos",
            getnames=True,
            guessingrows=100,
        ),
        [Column("sku", "String", source="catalog")],
        "tFileInputExcel_3",
        0,
        0,
    )

    assert any(p.codigo == "P-GUESSINGROWS" for p in resultado.pendientes)


def test_interprete_no_finge_ejecucion_de_archivo_xls():
    plan = Plan(program="programa.sas")
    plan.graph.add_operator(_operador(dbms="xls", outputs=["WORK.ventas"]))

    with pytest.raises(NoSoportadoEnInterprete) as error:
        ejecutar_plan(plan, {})

    assert error.value.kind == "xls"
    assert "97-2003" in error.value.detalle


def test_migracion_xlsx_emite_marcador_y_no_publica_hallazgos_secretos(tmp_path):
    caso = REPO / "tests/corpus/L0/l0_19_importar_xlsx_hoja"

    resultado = migrar(caso / "programa.sas", tmp_path / "salida", muestra=caso / "entradas")

    assert resultado.jobs
    assert "P-TIPO-EXCEL" in {p.codigo for p in resultado.pendientes}
    assert not escanear_ruta(resultado.carpeta).hallazgos
    item = next(resultado.carpeta.rglob("*.item")).read_text(encoding="utf-8")
    assert 'name="PASSWORD" value="&quot;sgm_ref&quot;"' in item
