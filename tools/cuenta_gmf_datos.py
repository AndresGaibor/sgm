"""Esperados y comparación de `v04_tipo_cta_gmf` para el arnés de R1-06 (hito 88).

La verdad plantada sale de `esperado/` y de `caso.yaml`; nunca se calcula con la salida del Job.
Los cuatro flujos se comparan **fila por fila por nombre de columna** (el caso declara
`orden_relevante: false`, así que se comparan como multisets). Además se comprueba el desglose de
anomalías plantadas y las tres invariantes del caso.

Salvedad que no se esconde: se comparan las **tablas** `esperado/*.csv`, no los archivos de
`esperado/archivos/`. Estos últimos son la salida supuesta de `PROC EXPORT` (sin cabecera, con
`;`, faltante vacío), y `caso.yaml` sigue en `pendiente_revision` precisamente porque el formato
de exportación no está demostrado con SAS.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v04_tipo_cta_gmf"
PRODUCTOS = ("CTE", "AHO")
MODOS = ("tipo_cta", "gmf", "valido", "cuenta")

# Cada flujo se compara contra la tabla que el SAS nombra en su CREATE TABLE.
ARCHIVOS = {
    "tipo_cta": "INCONS_TIPO_CTA_INVALIDO_{p}.csv",
    "gmf": "INCONS_GMF_INVALIDO_{p}.csv",
    "valido": "SABANA_VALIDA_{p}.csv",
    "cuenta": "INCONS_CUENTA_{p}.csv",
}
SALIDAS = {
    "tipo_cta": "tipo_cta.csv",
    "gmf": "gmf.csv",
    "valido": "validos.csv",
    "cuenta": "cuenta.csv",
}
MOTIVO_A_ANOMALIA = {
    "TIPO CTA INVALIDO": "tipo_cta_invalido",
    "GMF NO NUMERICO": "gmf_invalido",
    "GMF FUERA DE RANGO": "gmf_fuera_rango",
}


def _leer(ruta: Path, columnas: tuple[str, ...] | None = None) -> tuple[tuple[str, ...], ...]:
    """Filas de un CSV con cabecera, proyectadas a `columnas` si se dan."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo, delimiter=",")
        nombres = columnas or tuple(lector.fieldnames or ())
        filas = [tuple((fila.get(c) or "") for c in nombres) for fila in lector]
    return tuple(filas)


def _encabezado(ruta: Path) -> tuple[str, ...]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return tuple(next(csv.reader(archivo, delimiter=",")))


def esperado(producto: str) -> dict[str, tuple[tuple[str, ...], ...]]:
    """Filas esperadas de cada flujo, leídas de `esperado/`."""
    return {
        modo: _leer(CASO / "esperado" / nombre.format(p=producto))
        for modo, nombre in ARCHIVOS.items()
    }


def observado(salida: Path) -> dict[str, tuple[tuple[str, ...], ...]]:
    """Filas que escribió el Job, en el orden de columnas del esperado correspondiente."""
    resultado: dict[str, tuple[tuple[str, ...], ...]] = {}
    for modo, nombre in SALIDAS.items():
        columnas = _encabezado(CASO / "esperado" / ARCHIVOS[modo].format(p="CTE"))
        resultado[modo] = _leer(salida / nombre, columnas)
    return resultado


def anomalias(filas: tuple[tuple[str, ...], ...]) -> dict[str, int]:
    """Desglose por motivo de `INCONSISTENCIA` (última columna de la cuenta)."""
    conteo = Counter(MOTIVO_A_ANOMALIA.get(fila[-1], "desconocido") for fila in filas)
    return {clave: conteo[clave] for clave in MOTIVO_A_ANOMALIA.values()}


def anomalias_plantadas() -> dict[str, dict[str, int]]:
    """Conteos declarados en `caso.yaml`, por producto."""
    caso = yaml.safe_load((CASO / "caso.yaml").read_text(encoding="utf-8"))
    claves = (*MOTIVO_A_ANOMALIA.values(), "validos")
    return {
        producto: {clave: caso["anomalias_plantadas"][producto.lower()][clave] for clave in claves}
        for producto in PRODUCTOS
    }


def _conteos(nombre: str, columna: str) -> int:
    with (CASO / "esperado" / nombre).open(encoding="utf-8", newline="") as archivo:
        return sum(int(fila[columna]) for fila in csv.DictReader(archivo, delimiter=","))


def informe(producto: str, esp: dict, obs: dict) -> bool:
    """Compara los cuatro flujos fila por fila y el desglose de anomalías plantadas."""
    bueno = True
    for modo in MODOS:
        e, o = sorted(esp[modo]), sorted(obs[modo])
        cuadra = e == o
        bueno &= cuadra
        print(
            f"{producto} {modo}: esperadas {len(e)} filas, obtenidas {len(o)}; "
            f"{'OK' if cuadra else 'DIFERENCIA'}"
        )
        if not cuadra:
            print(f"  solo en esperado: {sorted(Counter(e) - Counter(o))[:3]}")
            print(f"  solo en obtenido: {sorted(Counter(o) - Counter(e))[:3]}")
    plantadas = anomalias_plantadas()[producto]
    obtenidas = {**anomalias(obs["cuenta"]), "validos": len(obs["valido"])}
    cuadra = obtenidas == plantadas
    bueno &= cuadra
    print(
        f"{producto} anomalías plantadas {plantadas}; obtenidas {obtenidas}; "
        f"{'OK' if cuadra else 'DIFERENCIA'}"
    )
    return bueno


def invariantes(resultados: dict[str, dict[str, tuple[tuple[str, ...], ...]]]) -> bool:
    """Las tres invariantes medibles del `caso.yaml`."""
    sabana = {p: len(_leer(CASO / "esperado" / f"SABANA_{p}.csv")) for p in PRODUCTOS}
    rechazos = {p: len(resultados[p]["cuenta"]) for p in PRODUCTOS}
    validos = {p: len(resultados[p]["valido"]) for p in PRODUCTOS}
    uno = all(sabana[p] == validos[p] + rechazos[p] for p in PRODUCTOS)
    dos = _conteos("CONTEO_CUENTA.csv", "NRO_RECHAZOS") == sum(rechazos.values())
    tres = _conteos("CONTEO_CUENTA_VALIDA.csv", "NRO_VALIDOS") == sum(validos.values())
    print(
        f"Invariantes: sábana=válidos+rechazos {'sí' if uno else 'NO'}; "
        f"conteo de rechazos={sum(rechazos.values())} frente a "
        f"{_conteos('CONTEO_CUENTA.csv', 'NRO_RECHAZOS')} {'sí' if dos else 'NO'}; "
        f"conteo de válidos={sum(validos.values())} frente a "
        f"{_conteos('CONTEO_CUENTA_VALIDA.csv', 'NRO_VALIDOS')} {'sí' if tres else 'NO'}"
    )
    return uno and dos and tres


__all__ = [
    "ARCHIVOS", "CASO", "MODOS", "MOTIVO_A_ANOMALIA", "PRODUCTOS", "SALIDAS",
    "anomalias", "anomalias_plantadas", "esperado", "informe", "invariantes", "observado",
]
