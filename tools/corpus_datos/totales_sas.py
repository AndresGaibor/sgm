"""Semántica de SAS que usan los casos L8 de totales, aplicada a las filas plantadas.

Cada función copia lo que hace el programa SAS del caso, no una regla ideal. Las tablas de salida
son pares `(columnas, filas)` con las filas como listas de valores en el orden de `columnas`.
Un faltante numérico es `None` (celda vacía en el CSV); un texto vacío de origen también.

Convención de escritura (PROC EXPORT DBMS=CSV, ver tests/corpus/L0/REVISION.md): separador `,`,
comillas solo si el texto las necesita, fin de línea `\\n`, decimales sin ceros sobrantes.
Supuesto no comprobado con SAS real: un número se escribe con formato BEST (sin `0` final).
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

Fila = dict[str, object]
Tabla = tuple[list[str], list[list[object]]]


def valor_numerico(celda: str) -> Decimal | None:
    """Lo que hace `input(left(x), 20.)`: quita blancos a la izquierda; vacío es faltante."""
    texto = celda.strip()
    return Decimal(texto) if texto else None


def con_form(filas: list[dict[str, str]]) -> list[dict[str, object]]:
    """DATA step `FORM_FIN_SALDO_CTA = input(left(FIN_SALDO_CTA), 20.)`: la variable va al final."""
    return [{**fila, "FORM_FIN_SALDO_CTA": valor_numerico(fila["FIN_SALDO_CTA"])} for fila in filas]


def suma(filas: list[dict[str, object]], columna: str = "FORM_FIN_SALDO_CTA") -> Decimal | None:
    """PROC SQL SUM: ignora faltantes; si todos faltan, el resultado es faltante (None)."""
    valores = [fila[columna] for fila in filas if fila[columna] is not None]
    if not valores:
        return None
    return sum(valores, Decimal("0"))


def celda(valor: object) -> str:
    """Texto de una celda para el CSV: faltante vacío, decimal sin ceros sobrantes."""
    if valor is None:
        return ""
    if isinstance(valor, Decimal):
        return "0" if valor == 0 else format(valor.normalize(), "f")
    return str(valor)


def tabla(columnas: list[str], filas: list[dict[str, object]]) -> Tabla:
    """Proyecta las filas a las columnas pedidas, en ese orden."""
    return columnas, [[fila[c] for c in columnas] for fila in filas]


def sin_duplicados_exactos(filas: list[dict], columnas: list[str]) -> list[dict]:
    """PROC SORT BY _ALL_ con NODUPREC: una fila por combinación idéntica, orden por todas."""
    vistos: dict[tuple, dict] = {}
    for fila in filas:
        vistos.setdefault(tuple(_clave(fila[c]) for c in columnas), fila)
    return [vistos[k] for k in sorted(vistos)]


def primera_por_llave(filas: list[dict], llave: list[str]) -> list[dict]:
    """PROC SORT BY llave + NODUPKEY (EQUALS, el valor por defecto): conserva la primera fila de
    cada llave en el orden de entrada, y el resultado queda ordenado por la llave."""
    primeras: dict[tuple, dict] = {}
    for fila in filas:
        primeras.setdefault(tuple(_clave(fila[c]) for c in llave), fila)
    return [primeras[k] for k in sorted(primeras)]


def _clave(valor: object) -> tuple:
    """Clave de orden: faltantes primero, luego números, luego texto (como el orden de SAS)."""
    if valor is None:
        return (0, Decimal(0), "")
    if isinstance(valor, Decimal):
        return (1, valor, "")
    return (2, Decimal(0), str(valor))


def escribir_tabla(carpeta: Path, nombre: str, columnas: list[str], filas: list[list]) -> Path:
    """Escribe `<carpeta>/<nombre>.csv` con encabezado y el formato de `celda`."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}.csv"
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(columnas)
        for fila in filas:
            escritor.writerow([celda(valor) for valor in fila])
    return ruta
