"""Pruebas de `tools/simular_insumos.py`: el xlsx que escribe se lee de vuelta con zipfile y ET."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _cargar_modulo():
    spec = importlib.util.spec_from_file_location(
        "simular_insumos", REPO / "tools" / "simular_insumos.py"
    )
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


simular = _cargar_modulo()


def _leer_hoja(ruta: Path) -> list[list[str]]:
    """Filas de `Sheet1` como texto, leídas desde el xlsx con zipfile y ElementTree."""
    with zipfile.ZipFile(ruta) as paquete:
        raiz = ElementTree.fromstring(paquete.read("xl/worksheets/sheet1.xml"))
    filas: list[list[str]] = []
    for fila in raiz.findall("m:sheetData/m:row", _NS):
        valores = []
        for celda in fila.findall("m:c", _NS):
            valores.append("".join(t.text or "" for t in celda.findall("m:is/m:t", _NS)))
        filas.append(valores)
    return filas


PROGRAMA = (
    "PROC IMPORT DATAFILE='\\\\srv\\carpeta\\Datos ñandú.xlsx' DBMS=EXCELCS "
    "OUT=WORK.Datos REPLACE;\nRUN;\n"
    "proc sql;\n"
    "  select d.'AÑO'n, d.MES, d.'Nombre & Apellido'n from WORK.Datos d;\n"
    "quit;\n"
    "PROC IMPORT DATAFILE='/ruta/Sin_uso.xlsx' DBMS=EXCELCS OUT=WORK.SinUso REPLACE;\nRUN;\n"
    "PROC IMPORT DATAFILE='/ruta/base.csv' DBMS=dlm OUT=WORK.Base REPLACE;\nRUN;\n"
    "proc sql; select b.X from WORK.Base b; quit;\n"
)


def test_cabecera_y_filas_simuladas_con_nombres_no_ascii(tmp_path):
    lineas = simular.generar(PROGRAMA, tmp_path, 3)

    destino = tmp_path / "Datos ñandú.xlsx"
    assert destino.exists()
    filas = _leer_hoja(destino)
    assert filas[0] == ["AÑO", "MES", "Nombre & Apellido"]
    assert len(filas) == 1 + 3
    assert filas[1] == ["SIM_AÑO_1", "SIM_MES_1", "SIM_Nombre & Apellido_1"]
    assert filas[3][0] == "SIM_AÑO_3"
    assert any("Datos ñandú.xlsx" in linea for linea in lineas)


def test_sin_columnas_usadas_escribe_solo_pendiente_sin_datos(tmp_path):
    simular.generar(PROGRAMA, tmp_path, 5)

    filas = _leer_hoja(tmp_path / "Sin_uso.xlsx")
    assert filas == [["PENDIENTE"]]


def test_solo_escribe_archivos_excel_y_una_linea_por_archivo(tmp_path):
    lineas = simular.generar(PROGRAMA, tmp_path, 2)

    escritos = sorted(p.name for p in tmp_path.iterdir())
    assert escritos == ["Datos ñandú.xlsx", "Sin_uso.xlsx"]
    assert len(lineas) == 2


def test_filas_cero_deja_solo_la_cabecera(tmp_path):
    simular.generar(PROGRAMA, tmp_path, 0)

    filas = _leer_hoja(tmp_path / "Datos ñandú.xlsx")
    assert filas == [["AÑO", "MES", "Nombre & Apellido"]]


def test_paquete_tiene_las_partes_del_xlsx_minimo(tmp_path):
    simular.generar(PROGRAMA, tmp_path, 1)

    with zipfile.ZipFile(tmp_path / "Datos ñandú.xlsx") as paquete:
        nombres = set(paquete.namelist())
        libro = paquete.read("xl/workbook.xml").decode("utf-8")
    assert nombres == {
        "[Content_Types].xml",
        "_rels/.rels",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
        "xl/worksheets/sheet1.xml",
    }
    assert 'name="Sheet1"' in libro


def test_letras_de_columna_pasan_de_z_a_aa():
    assert simular._letra(0) == "A"
    assert simular._letra(25) == "Z"
    assert simular._letra(26) == "AA"
    assert simular._letra(27) == "AB"


def test_escribir_xlsx_escapa_xml_en_cabecera_y_datos(tmp_path):
    destino = tmp_path / "salida.xlsx"
    simular.escribir_xlsx(destino, ["A<B", "C&D"], [["<x>", "y&z"]])

    assert _leer_hoja(destino) == [["A<B", "C&D"], ["<x>", "y&z"]]


def test_linea_de_comando_con_el_programa_grande(tmp_path):
    resultado = subprocess.run(
        [sys.executable, str(REPO / "tools" / "simular_insumos.py"), str(FIXTURE), str(tmp_path)],
        capture_output=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr.decode("utf-8", errors="replace")

    validacion = _leer_hoja(tmp_path / "Validacion_fecha.xlsx")
    assert validacion[0] == ["AÑO", "MES", "DIA"]
    assert len(validacion) == 1 + 5
    homologacion = _leer_hoja(tmp_path / "Homologacion_tpo_dto.xlsx")
    assert "CNAME" in homologacion[0]
    assert len(homologacion) == 1 + 5


@pytest.mark.parametrize("filas", ["-1"])
def test_linea_de_comando_rechaza_filas_negativas(tmp_path, filas):
    with pytest.raises(SystemExit):
        simular.main([str(FIXTURE), str(tmp_path), "--filas", filas])
