"""Hito 100d / R2-02 (parte 2): datos de entrada y oráculo independiente de los totales.

El oráculo calcula, con `csv`, `zipfile` y `Decimal`, lo que el `job_producto` emitido debe escribir
en `totales_origen_<p>.csv` y `totales_salida_<p>.csv`. No usa el Job ni el productor de `tools/`:

* origen: todas las filas; conteo de filas, de saldos no vacíos y suma de esos saldos (un
  faltante no suma; un campo en blanco es faltante).
* salida: las filas cuyo `TIPO_DOC` está en la homologación (columna `CNAME` de la hoja 1).
  Es la definición "saldos validados" de la sección 1.2 del manual.

Codificación de `TIPO_DOC`: el SAS declara `TIPO_DOC` numérico (`input(left(VAR9), 8.)`), así que
el Job normaliza la columna con ese informat y `TD01` queda vacío (hito 85, R1-03 pendiente). Para
que la prueba mida totales y no esa salvedad, los códigos `TD01`..`TD04` del corpus se escriben
como `1`..`4` y el Excel de homologación se genera con los mismos valores numéricos. Un código
`9` no está homologado y es el rechazo plantado.

Escenarios (`preparar_origen`):
* `tal_cual`: el origen de `L8/validaciones/v05_codex_saldos` con los códigos numéricos.
* `planta`: el mismo origen de CTE con `TIPO_DOC` `9` en una fila (`FILA_PLANTADA`).
"""

from __future__ import annotations

import csv
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v05_codex_saldos"
HOMOLOGACION_CORPUS = (
    REPO / "tests" / "corpus" / "L8" / "validaciones" / "v01_tipo_doc" / "entradas"
    / "Homologacion_tpo_dto.xlsx"
)  # fmt: skip
ARCHIVO_HOMOLOGACION = "Homologacion_numerica.xlsx"
PRODUCTOS = ("CTE", "AHO")
PERIODO = ("2026", "10", "01")  # fecha del Job: periodo_anio, periodo_mes y periodo_dia
TOLERANCIA = Decimal("0.005")  # `tolerancia` de `L8/totales/04/caso.yaml`
TIPO_DOC = 8  # posición de TIPO_DOC en el CSV de 23 campos
SALDO = 22  # posición de FIN_SALDO_CTA
CODIGOS = {"TD01": "1", "TD02": "2", "TD03": "3", "TD04": "4"}
TIPO_NO_HOMOLOGADO = "9"
FILA_PLANTADA = 4  # quinta fila de CTE: su saldo es la diferencia que debe aparecer
CABECERA_TOTALES = ["PRODUCTO", "TIPO", "NRO_FILAS", "NRO_SALDOS_NO_VACIOS", "SUMA_SALDO"]
_HOJA = "xl/worksheets/sheet1.xml"
_ESPACIO = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _leer(ruta: Path) -> list[list[str]]:
    with ruta.open(encoding="utf-8", newline="") as entrada:
        return [fila for fila in csv.reader(entrada, delimiter=";") if fila]


def preparar_origen(trabajo: Path, producto: str, planta: bool) -> Path:
    """Escribe en `trabajo` el origen de `producto` con códigos numéricos y la fila plantada."""
    filas = [list(f) for f in _leer(CASO / "entradas" / f"DETALLE_{producto}.csv")]
    for fila in filas:
        fila[TIPO_DOC] = CODIGOS.get(fila[TIPO_DOC].strip(), fila[TIPO_DOC])
    if planta:
        filas[FILA_PLANTADA][TIPO_DOC] = TIPO_NO_HOMOLOGADO
    ruta = trabajo / f"DETALLE_{producto}_{'planta' if planta else 'tal_cual'}.csv"
    with ruta.open("w", encoding="utf-8", newline="") as salida:
        csv.writer(salida, delimiter=";", lineterminator="\n").writerows(filas)
    return ruta


def homologacion_numerica(trabajo: Path) -> Path:
    """Excel de homologación con `CNAME` 1..4 (numéricos), igual al del corpus en lo demás."""
    destino = trabajo / ARCHIVO_HOMOLOGACION
    hoja = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        '<row r="1"><c r="A1" t="inlineStr"><is><t>CNAME</t></is></c></row>'
    )
    for indice, codigo in enumerate(sorted(CODIGOS.values()), start=2):
        hoja += f'<row r="{indice}"><c r="A{indice}"><v>{codigo}</v></c></row>'
    hoja += "</sheetData></worksheet>"
    with zipfile.ZipFile(HOMOLOGACION_CORPUS) as origen:
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as salida:
            for nombre in origen.namelist():
                contenido = hoja.encode("utf-8") if nombre == _HOJA else origen.read(nombre)
                salida.writestr(nombre, contenido)
    return destino


def homologados(libro: Path) -> set[str]:
    """Valores de la columna `CNAME` (A, sin la cabecera) de la hoja 1, texto o número."""
    import xml.etree.ElementTree as ET

    with zipfile.ZipFile(libro) as archivo:
        raiz = ET.fromstring(archivo.read(_HOJA))
    valores: set[str] = set()
    for celda in raiz.iter(f"{_ESPACIO}c"):
        referencia = celda.get("r", "")
        if not referencia.startswith("A") or referencia == "A1":
            continue
        texto = "".join(t.text or "" for t in celda.iter(f"{_ESPACIO}t"))
        valor = celda.find(f"{_ESPACIO}v")
        valores.add((texto or (valor.text if valor is not None else "")).strip())
    return valores


def saldo(texto: str) -> Decimal | None:
    """Saldo de la fila: vacío o no numérico es faltante (None)."""
    try:
        return Decimal(texto.strip())
    except InvalidOperation:
        return None


def _totales(filas: list[list[str]]) -> dict[str, object]:
    valores = [saldo(f[SALDO]) for f in filas]
    no_vacios = [v for v in valores if v is not None]
    return {
        "NRO_FILAS": len(filas),
        "NRO_SALDOS_NO_VACIOS": len(no_vacios),
        "SUMA_SALDO": sum(no_vacios, Decimal("0")),
    }


def esperado_totales(origen: Path, validos: set[str]) -> dict[str, dict[str, object]]:
    """Origen: todas las filas. Salida: las de `TIPO_DOC` homologado, sin conteo de saldos."""
    filas = _leer(origen)
    salida = _totales([f for f in filas if f[TIPO_DOC].strip() in validos])
    salida["NRO_SALDOS_NO_VACIOS"] = None  # la salida no define este conteo (caso 04)
    return {"origen": _totales(filas), "salida": salida}


def coincide(obtenido: str, esperado: object) -> bool:
    """Compara un campo de texto de un archivo de totales con el valor del oráculo."""
    if esperado is None:
        return obtenido == ""
    if isinstance(esperado, Decimal):
        try:
            return abs(Decimal(obtenido) - esperado) <= TOLERANCIA
        except InvalidOperation:
            return False
    return obtenido == str(esperado)
