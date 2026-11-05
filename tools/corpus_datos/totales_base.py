"""Genera las entradas y el `caso.yaml` de los casos L8 de totales (`tests/corpus/L8/totales`).

Uso: uv run python tools/corpus_datos/totales.py [carpeta_destino] (los casos viven en totales.py).

Todo es ficticio y evidente: cuentas `SIM...`, nombres `SIM LLAVE ...`, saldos inventados. La
semilla es fija, así que la salida es idéntica en cada ejecución. Cada caso declara en
`anomalias_plantadas` lo que este generador plantó; esos conteos son el oráculo independiente que
`tests/unit/test_corpus_totales.py` vuelve a comprobar contando desde los CSV.

El estilo de los programas SAS (no incluido aquí) sigue `client_large.sas`: el archivo de producto
es delimitado con `;`, sin cabecera, de 23 columnas. Sus nombres por posición están en `COLUMNAS`.
"""

from __future__ import annotations

import io
import random
import zipfile
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "tests" / "corpus" / "L8" / "totales"
SEMILLA = 20261104

# Nombres por posición (VAR1..VAR23). El programa SAS los renombra con PROC SQL.
COLUMNAS = (
    "ANIO_PROCESO", "MES_PROCESO", "CODIGO_OFICINA", "RELACION", "CODIGO_SUCURSAL",
    "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
    "VAL_CRED_MES", "NRO_CRED_MES", "PROM_CRED_MES", "MED_CRED_MES", "VAL_DEB_MES",
    "NRO_DEB_MES", "PROM_DEB_MES", "MED_SALDO_CTA", "PROM_SALDO_CTA", "MAX_SALDO_CTA",
    "MIN_SALDO_CTA", "FIN_SALDO_CTA",
)  # fmt: skip
TIPOS_VALIDOS = ("CC", "TI", "CE", "PA")
FECHA = {"ANIO": 2026, "MES": 9, "DIA": 30}

Fila = dict[str, str]


def base(prod: str, i: int, saldo: str, **cambios: str) -> Fila:
    """Fila de producto ficticia y válida. Los `cambios` planta una anomalía concreta."""
    cod = "1" if prod == "CTE" else "2"
    fila = dict.fromkeys(COLUMNAS, "0.00")
    fila.update(
        ANIO_PROCESO="2026", MES_PROCESO="09", CODIGO_OFICINA="OF01", RELACION="T",
        CODIGO_SUCURSAL="SU1", TIPO_CTA="01", NRO_CTA=f"{cod}{i:08d}",
        LLAVE_NOMBRE=f"SIM LLAVE {prod} {i:03d}", TIPO_DOC="CC", NRO_DOC=f"SIM{prod}{i:05d}",
        GMF="S", FIN_SALDO_CTA=saldo,
    )  # fmt: skip
    fila.update(cambios)
    return fila


def saldo(rng: random.Random) -> str:
    """Saldo con dos decimales y punto, como lo deja el CSV del origen."""
    c = rng.randint(10_000, 900_000)
    return f"{c // 100}.{c % 100:02d}"


def suma(filas: list[Fila]) -> str:
    """Suma exacta de FIN_SALDO_CTA ignorando vacíos, con dos decimales (como SUM de SAS)."""
    total = sum((Decimal(f["FIN_SALDO_CTA"].strip()) for f in filas if f["FIN_SALDO_CTA"].strip()),
                Decimal("0"))  # fmt: skip
    return f"{total:.2f}"


def csv_bytes(filas: list[Fila]) -> bytes:
    lineas = [";".join(f[c] for c in COLUMNAS) for f in filas]
    return ("\n".join(lineas) + "\n").encode("utf-8")


def xlsx_bytes(filas: list[list[str | int]]) -> bytes:
    """Libro .xlsx mínimo (una hoja, cadenas en línea), con fechas fijas para ser reproducible."""
    filas_xml = []
    for r, fila in enumerate(filas, 1):
        celdas = []
        for c, valor in enumerate(fila):
            ref = f"{chr(65 + c)}{r}"
            if isinstance(valor, int):
                celdas.append(f'<c r="{ref}"><v>{valor}</v></c>')
            else:
                celdas.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(valor)}</t></is></c>')
        filas_xml.append(f'<row r="{r}">{"".join(celdas)}</row>')
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    partes = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
            'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{rel}/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{ns}" '
            f'xmlns:r="{rel}"><sheets><sheet name="Hoja1" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>"
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{rel}/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>"
        ),
        "xl/worksheets/sheet1.xml": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{ns}">'
            f'<sheetData>{"".join(filas_xml)}</sheetData></worksheet>'
        ),
    }


    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, contenido in partes.items():
            info = zipfile.ZipInfo(nombre, date_time=(2026, 11, 4, 0, 0, 0))
            z.writestr(info, contenido.encode("utf-8"))
    return buffer.getvalue()


def fecha_xlsx() -> bytes:
    """Excel de periodo: una fila con AÑO, MES y DIA (el que el programa lee)."""
    return xlsx_bytes([["AÑO", "MES", "DIA"], [FECHA["ANIO"], FECHA["MES"], FECHA["DIA"]]])


def caso(id_: str, tema: str, construcciones: list[str], productos: list[str], **resto) -> dict:
    """Plantilla común del `caso.yaml`. `resto` trae anomalías, salidas, supuestos y fuentes."""
    datos = {
        "id": id_,
        "nivel": "L8",
        "tema": tema,
        "construcciones": construcciones,
        "productos": productos,
        "capa": "A (SQL ejecutable en SQLite) y B (funciones input, left, put; vectores citados)",
        "estado": "sin_esperado",
    }
    datos.update(resto)
    return datos


FUENTES_SAS = [
    "https://support.sas.com/documentation/cdl/en/proc/65145/HTML/default/"
    "p1holnuvm8kon1n1wwhvrjnrab65.htm",  # PROC SORT, NODUPKEY y NODUPREC
    "https://support.sas.com/documentation/cdl/en/proc/65145/HTML/default/"
    "n0ku4pxzx3d2len10ozjgyjbrpl9.htm",  # PROC EXPORT
    "https://support.sas.com/documentation/cdl/en/acpcref/63181/HTML/default/"
    "n06lm371ac8dj6n17xrbr5fofcgb.htm",  # pass-through: CONNECT, CONNECTION TO, DISCONNECT
    "https://go.documentation.sas.com/api/docsets/acreldb/9.4/content/"
    "n0l3rcy5ljom1ln1o34eq22rzedg.htm",  # SQL pass-through para Impala
]

