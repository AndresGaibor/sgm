"""Escribe libros XLSX OOXML pequeños y reproducibles para el corpus sintético."""

from __future__ import annotations

import math
import re
import zipfile
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

_NOMBRE_HOJA_INVALIDO = re.compile(r"[\\/*?:\[\]]")


def _letras_columna(numero: int) -> str:
    letras = ""
    while numero:
        numero, resto = divmod(numero - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def _numero(valor: object) -> str:
    if isinstance(valor, bool):
        raise ValueError("el generador no acepta booleanos como números")
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise ValueError(f"valor numérico XLSX no válido: {valor!r}") from None
    if not numero.is_finite():
        raise ValueError("el generador no acepta NaN ni infinitos")
    texto = format(numero.normalize(), "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return "0" if texto in {"", "-0"} else texto


def _celda(valor: object, referencia: str) -> str:
    ref = quoteattr(referencia)
    if valor is None:
        return f'<c r={ref}/>'
    if isinstance(valor, bool):
        return f'<c r={ref} t="b"><v>{int(valor)}</v></c>'
    if isinstance(valor, (int, float, Decimal)):
        if isinstance(valor, float) and not math.isfinite(valor):
            raise ValueError("el generador no acepta NaN ni infinitos")
        return f'<c r={ref}><v>{_numero(valor)}</v></c>'
    if isinstance(valor, str):
        espacio = ' xml:space="preserve"' if valor != valor.strip() else ""
        return f'<c r={ref} t="inlineStr"><is><t{espacio}>{escape(valor)}</t></is></c>'
    raise ValueError(f"tipo de celda XLSX no soportado: {type(valor).__name__}")


def _hoja_xml(filas: Sequence[Sequence[object]]) -> str:
    filas_xml = []
    for indice_fila, fila in enumerate(filas, start=1):
        celdas = "".join(
            _celda(valor, f"{_letras_columna(indice_columna)}{indice_fila}")
            for indice_columna, valor in enumerate(fila, start=1)
        )
        filas_xml.append(f'<row r="{indice_fila}">{celdas}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(filas_xml)}</sheetData></worksheet>"
    )


def escribir_xlsx(ruta: Path, hojas: Mapping[str, Sequence[Sequence[object]]]) -> None:
    """Escribe hojas de texto y números con metadatos ZIP fijos para comparar bytes."""
    if not hojas:
        raise ValueError("el libro debe tener al menos una hoja")
    nombres = list(hojas)
    if any(
        not isinstance(nombre, str)
        or not nombre
        or len(nombre) > 31
        or _NOMBRE_HOJA_INVALIDO.search(nombre)
        for nombre in nombres
    ):
        raise ValueError("nombre de hoja XLSX inválido")
    if len({nombre.casefold() for nombre in nombres}) != len(nombres):
        raise ValueError("nombres de hoja duplicados sin distinguir mayúsculas")

    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        + "".join(
            f"<sheet name={quoteattr(nombre)} sheetId=\"{indice}\" r:id=\"rId{indice}\"/>"
            for indice, nombre in enumerate(nombres, start=1)
        )
        + "</sheets></workbook>"
    )
    relaciones = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{indice}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{indice}.xml"/>'
            for indice in range(1, len(nombres) + 1)
        )
        + "</Relationships>"
    )
    tipos = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + "".join(
            f'<Override PartName="/xl/worksheets/sheet{indice}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for indice in range(1, len(nombres) + 1)
        )
        + "</Types>"
    )
    raiz_relaciones = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    partes = [
        ("[Content_Types].xml", tipos),
        ("_rels/.rels", raiz_relaciones),
        ("xl/workbook.xml", workbook),
        ("xl/_rels/workbook.xml.rels", relaciones),
        *(
            (f"xl/worksheets/sheet{indice}.xml", _hoja_xml(hojas[nombre]))
            for indice, nombre in enumerate(nombres, start=1)
        ),
    ]
    with zipfile.ZipFile(ruta, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archivo:
        for nombre, contenido in partes:
            info = zipfile.ZipInfo(nombre, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            archivo.writestr(info, contenido.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
