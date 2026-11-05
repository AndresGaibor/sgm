"""Ayudas de `prueba_conciliacion_caso.py` (hito 98d): entradas y comparación con `esperado/`.

Los totales de entrada salen de `esperado/TOTALES_CONC_<p>.csv` del caso L8/totales/05: el origen
es `NRO_ORIGEN` y `SUMA_ORIGEN`; la salida es válidos más rechazados (`NRO_VALIDOS` +
`NRO_RECHAZADOS` y `SUMA_VALIDOS` + `SUMA_RECHAZADOS`), como en `CONCILIACION_*` del SAS.
"""

from __future__ import annotations

import csv
import re
from decimal import Decimal
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests/corpus/L8/totales/05_conciliacion"
FECHA = ("2026", "09", "30")  # valores de prueba: el caso no declara la fecha del proceso
PRODUCTOS = ("CTE", "AHO")
CABECERA_TOTALES = ["PRODUCTO", "TIPO", "NRO_FILAS", "NRO_SALDOS_NO_VACIOS", "SUMA_SALDO"]


def _primera_fila(archivo: Path) -> dict[str, str]:
    """Primera fila de un CSV con cabecera, como diccionario."""
    with archivo.open(encoding="utf-8", newline="") as entrada:
        return next(csv.DictReader(entrada))


def _escribir_csv(archivo: Path, filas: list[list[str]]) -> None:
    """CSV con `;`, cabecera de totales y una fila por producto y tipo."""
    with archivo.open("w", encoding="utf-8", newline="") as salida:
        escritor = csv.writer(salida, delimiter=";", lineterminator="\n")
        escritor.writerow(CABECERA_TOTALES)
        escritor.writerows(filas)


def escribir_totales(carpeta: Path) -> None:
    """Escribe `totales_origen_<p>.csv` y `totales_salida_<p>.csv` de cada producto en `carpeta`."""
    for producto in PRODUCTOS:
        fila = _primera_fila(CASO / "esperado" / f"TOTALES_CONC_{producto}.csv")
        filas_salida = int(fila["NRO_VALIDOS"]) + int(fila["NRO_RECHAZADOS"])
        suma_salida = Decimal(fila["SUMA_VALIDOS"]) + Decimal(fila["SUMA_RECHAZADOS"])
        # NRO_SALDOS_NO_VACIOS va vacío: la conciliación no lo usa y el caso no lo define.
        _escribir_csv(
            carpeta / f"totales_origen_{producto}.csv",
            [[producto, "origen", fila["NRO_ORIGEN"], "", fila["SUMA_ORIGEN"]]],
        )
        _escribir_csv(
            carpeta / f"totales_salida_{producto}.csv",
            [[producto, "salida", str(filas_salida), "", f"{suma_salida:f}"]],
        )


def esperado(productos: tuple[str, ...]) -> list[tuple[str, int, Decimal]]:
    """Filas de `CONCILIACION_FINAL` del caso (producto, diferencia de filas, de saldo)."""
    filas = []
    with (CASO / "esperado" / "CONCILIACION_FINAL.csv").open(encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if fila["PRODUCTO"] in productos:
                filas.append((fila["PRODUCTO"], int(fila["DIF_FILAS"]), Decimal(fila["DIF_SALDO"])))
    return filas


def tolerancia() -> Decimal:
    """Tolerancia de comparación de `caso.yaml` (solo para comparar decimales, no de negocio)."""
    datos = yaml.safe_load((CASO / "caso.yaml").read_text(encoding="utf-8"))
    return Decimal(str(datos["tolerancia"]))


def comparar(archivo: Path, productos: tuple[str, ...]) -> list[str]:
    """Compara `conciliacion_<fecha>.csv` con lo esperado para `productos`. Vacío = coincide."""
    with archivo.open(encoding="utf-8", newline="") as f:
        obtenidas = list(csv.reader(f, delimiter=";"))
    cabecera, filas = obtenidas[0], obtenidas[1:]
    diferencias: list[str] = []
    if cabecera != ["PRODUCTO", "DIF_FILAS", "DIF_SALDO"]:
        diferencias.append(f"cabecera {cabecera} en lugar de PRODUCTO;DIF_FILAS;DIF_SALDO")
    previstas = esperado(productos)
    if len(filas) != len(previstas):
        diferencias.append(f"filas: {len(filas)} obtenidas, {len(previstas)} esperadas")
    tol = tolerancia()
    for (producto, dif_filas, dif_saldo), fila in zip(previstas, filas, strict=False):
        if fila[0] != producto:
            diferencias.append(f"orden: {fila[0]} en lugar de {producto}")
        if int(fila[1]) != dif_filas:
            diferencias.append(f"{producto} DIF_FILAS: {fila[1]} != {dif_filas}")
        if abs(Decimal(fila[2]) - dif_saldo) > tol:
            diferencias.append(f"{producto} DIF_SALDO: {fila[2]} != {dif_saldo} (tol {tol})")
    return diferencias


def proyecto_tecnico(proyecto: Path) -> str:
    """Nombre técnico del proyecto Talend (`technicalLabel` de `talend.project`)."""
    texto = (proyecto / "talend.project").read_text(encoding="utf-8", errors="replace")
    coincide = re.search(r'technicalLabel="([^"]+)"', texto)
    return coincide.group(1) if coincide else proyecto.name
