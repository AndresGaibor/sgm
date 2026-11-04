"""Simulador de insumos: un xlsx de muestra por cada Excel que importa el programa SAS.

Uso:
    uv run python tools/simular_insumos.py <programa.sas> <carpeta_salida> [--filas N]

Para cada `PROC IMPORT` de un archivo Excel escribe `<carpeta_salida>/<nombre>.xlsx` con una hoja
`Sheet1`. La fila 1 son las columnas que el programa demuestra (`columnas_por_importacion`) y
siguen N filas de datos simulados `SIM_<columna>_<n>`. Nunca se copian datos reales. Si el
programa no usa ninguna columna del archivo, el xlsx tiene solo la cabecera `PENDIENTE`.

El xlsx se escribe solo con la biblioteca estándar (zipfile y XML mínimo con cadenas en línea).
"""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from sgm.proceso.columnas_fuente import columnas_por_importacion

EXTENSIONES_EXCEL = (".xlsx", ".xls")
CABECERA_PENDIENTE = "PENDIENTE"

_NS_HOJA = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_RELACION = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PAQUETE = "http://schemas.openxmlformats.org/package/2006/content-types"
_NS_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CABECERA_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def nombre_salida(ruta: str) -> str:
    """Nombre del xlsx de salida: el nombre del archivo de origen con extensión `.xlsx`."""
    base = re.split(r"[\\/]", ruta)[-1]
    return Path(base).stem + ".xlsx"


def filas_simuladas(columnas: list[str], filas: int) -> list[list[str]]:
    """Datos evidentemente falsos: `SIM_<columna>_<n>` para n = 1..filas."""
    return [[f"SIM_{columna}_{n}" for columna in columnas] for n in range(1, filas + 1)]


def _letra(indice: int) -> str:
    """Letra de columna de Excel para un índice base 0 (0 = A, 26 = AA)."""
    letras = ""
    indice += 1
    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(ord("A") + resto) + letras
    return letras


def _hoja_xml(filas: list[list[str]]) -> str:
    renglones: list[str] = []
    for numero, fila in enumerate(filas, 1):
        celdas = "".join(
            f'<c r="{_letra(indice)}{numero}" t="inlineStr">'
            f'<is><t xml:space="preserve">{escape(valor)}</t></is></c>'
            for indice, valor in enumerate(fila)
        )
        renglones.append(f'<row r="{numero}">{celdas}</row>')
    return (
        _CABECERA_XML + f'<worksheet xmlns="{_NS_HOJA}">'
        f"<sheetData>{''.join(renglones)}</sheetData></worksheet>"
    )


def _partes_xlsx(filas: list[list[str]]) -> dict[str, str]:
    """Contenido de cada parte del paquete xlsx, por nombre de parte."""
    contenido = _CABECERA_XML + (
        f'<Types xmlns="{_NS_PAQUETE}">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
        'relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    raiz = _CABECERA_XML + (
        f'<Relationships xmlns="{_NS_RELS}">'
        f'<Relationship Id="rId1" Type="{_NS_RELACION}/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    libro = _CABECERA_XML + (
        f'<workbook xmlns="{_NS_HOJA}" xmlns:r="{_NS_RELACION}">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    relaciones_libro = _CABECERA_XML + (
        f'<Relationships xmlns="{_NS_RELS}">'
        f'<Relationship Id="rId1" Type="{_NS_RELACION}/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    return {
        "[Content_Types].xml": contenido,
        "_rels/.rels": raiz,
        "xl/workbook.xml": libro,
        "xl/_rels/workbook.xml.rels": relaciones_libro,
        "xl/worksheets/sheet1.xml": _hoja_xml(filas),
    }


def escribir_xlsx(destino: Path, cabecera: list[str], filas: list[list[str]]) -> None:
    """Escribe un xlsx de una hoja `Sheet1`: la cabecera en la fila 1 y `filas` debajo."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabla = [cabecera, *filas]
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as paquete:
        for nombre, xml in _partes_xlsx(tabla).items():
            paquete.writestr(nombre, xml.encode("utf-8"))


def generar(texto: str, carpeta: Path, filas: int) -> list[str]:
    """Escribe un xlsx por cada Excel importado y devuelve una línea de reporte por archivo."""
    lineas: list[str] = []
    escritos: set[str] = set()
    for ruta, columnas in columnas_por_importacion(texto).items():
        if not ruta.lower().endswith(EXTENSIONES_EXCEL):
            continue
        nombre = nombre_salida(ruta)
        if nombre in escritos:
            lineas.append(f"omitido {ruta}: el mismo nombre de archivo ya se escribió")
            continue
        escritos.add(nombre)
        if columnas:
            cabecera, cuerpo = columnas, filas_simuladas(columnas, filas)
            resumen = f"{len(columnas)} columnas, {len(cuerpo)} filas simuladas"
        else:
            cabecera, cuerpo = [CABECERA_PENDIENTE], []
            resumen = "PENDIENTE: el programa no usa columnas de este archivo"
        escribir_xlsx(carpeta / nombre, cabecera, cuerpo)
        lineas.append(f"{nombre}: {resumen} (origen {ruta})")
    return lineas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera xlsx simulados de los insumos Excel.")
    parser.add_argument("programa", type=Path, help="Programa SAS a analizar")
    parser.add_argument("carpeta", type=Path, help="Carpeta donde escribir los xlsx")
    parser.add_argument("--filas", type=int, default=5, help="Filas simuladas por archivo")
    args = parser.parse_args(argv)
    if args.filas < 0:
        parser.error("--filas no puede ser negativo")
    texto = args.programa.read_text(encoding="utf-8", errors="replace")
    for linea in generar(texto, args.carpeta, args.filas):
        print(linea)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
