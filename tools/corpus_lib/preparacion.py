"""Preparación tipo DATA step antes del PROC SQL, para casos que mezclan ambos pasos.

El oráculo SQL no ejecuta pasos DATA. Un caso que los necesita declara en `caso.yaml` un bloque
`preparacion`: cada asignación `variable = f1(f2(columna))` se evalúa con `evaluar` de
`tools/corpus_semantica_funciones.py` (capa B). El generador escribe el resultado en
`entradas_preparadas/<destino>.csv`, y el oráculo comprueba que ese archivo sigue siendo el que da
la preparación antes de usarlo como entrada del SQL.

Forma en el yaml:

    preparacion:
      origen: columnas_depositos        # entradas/columnas_depositos.csv
      destino: FORM_SALDO_CTA_CTE       # entradas_preparadas/FORM_SALDO_CTA_CTE.csv
      asignaciones:
        - variable: FORM_FIN_SALDO_CTA
          columna: FIN_SALDO_CTA
          pasos:                        # cada paso: [funcion, argumentos extra...]
            - [left]                    # left(valor)
            - [input, 20, 0]            # input(valor, 20, 0)

El valor de entrada de un faltante de texto es blanco, como en SAS. Un resultado faltante sale como
celda vacía. Solo se admiten funciones de la capa B.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from corpus_semantica_funciones import FUNCIONES, Faltante, evaluar

from .csv_tabla import Tabla, comparar_con_guardado, escribir_csv, leer_entradas

_IDENTIFICADOR = re.compile(r"[A-Za-z_]\w*$")


@dataclass(frozen=True)
class Asignacion:
    """Una asignación del DATA step: `variable` toma el resultado de `pasos` sobre `columna`."""

    variable: str
    columna: str
    pasos: tuple[tuple, ...]


@dataclass(frozen=True)
class Preparacion:
    """Preparación completa de un caso: tabla de origen, tabla destino y asignaciones."""

    origen: str
    destino: str
    asignaciones: tuple[Asignacion, ...]


def validar(dato: object) -> Preparacion:
    """Lee el bloque `preparacion` del yaml. Un dato mal formado es un ValueError con el motivo."""
    if not isinstance(dato, dict):
        raise ValueError("'preparacion' debe ser un mapa")
    lista = dato.get("asignaciones")
    if not isinstance(lista, list) or not lista:
        raise ValueError("'preparacion.asignaciones' debe ser una lista no vacía")
    return Preparacion(
        origen=_nombre(dato, "origen"),
        destino=_nombre(dato, "destino"),
        asignaciones=tuple(_asignacion(item) for item in lista),
    )


def _nombre(dato: dict, clave: str) -> str:
    valor = dato.get(clave)
    if not isinstance(valor, str) or not _IDENTIFICADOR.match(valor):
        raise ValueError(f"'preparacion.{clave}' debe ser un identificador")
    return valor


def _asignacion(item: object) -> Asignacion:
    if not isinstance(item, dict):
        raise ValueError("cada asignación de 'preparacion' debe ser un mapa")
    pasos = item.get("pasos")
    if not isinstance(pasos, list) or not pasos:
        raise ValueError("cada asignación necesita 'pasos' como lista no vacía")
    return Asignacion(
        variable=_nombre(item, "variable"),
        columna=_nombre(item, "columna"),
        pasos=tuple(_paso(paso) for paso in pasos),
    )


def _paso(paso: object) -> tuple:
    if not isinstance(paso, list) or not paso or not isinstance(paso[0], str):
        raise ValueError("cada paso es una lista [funcion, argumentos extra...]")
    if paso[0] not in FUNCIONES:
        raise ValueError(f"función no implementada en la capa B: {paso[0]}")
    for argumento in paso[1:]:
        if isinstance(argumento, bool) or not isinstance(argumento, (int, float, str)):
            raise ValueError(f"argumento no válido en el paso {paso[0]}: {argumento!r}")
    return tuple(paso)


def aplicar(origen: Tabla, prep: Preparacion) -> Tabla:
    """Aplica las asignaciones en orden y devuelve la tabla destino (origen más las variables)."""
    columnas = list(origen.columnas)
    tipos = list(origen.tipos)
    filas = [list(fila) for fila in origen.filas]
    for asignacion in prep.asignaciones:
        if asignacion.columna not in columnas:
            raise ValueError(f"la columna '{asignacion.columna}' no existe en el origen")
        entrada = columnas.index(asignacion.columna)
        nuevos = [_calcular(fila[entrada], asignacion.pasos) for fila in filas]
        if asignacion.variable in columnas:
            destino = columnas.index(asignacion.variable)
        else:
            columnas.append(asignacion.variable)
            tipos.append("TEXT")
            destino = len(columnas) - 1
            for fila in filas:
                fila.append(None)
        for fila, valor in zip(filas, nuevos, strict=True):
            fila[destino] = valor
        tipos[destino] = _tipo(nuevos)
    return Tabla(columnas, [tuple(fila) for fila in filas], tipos)


def _calcular(valor: object, pasos: tuple[tuple, ...]) -> object:
    actual = "" if valor is None else valor
    for paso in pasos:
        if isinstance(actual, Faltante):
            return None
        actual = evaluar(paso[0], actual, *paso[1:])
    return None if isinstance(actual, Faltante) else actual


def _tipo(valores: list[object]) -> str:
    presentes = [valor for valor in valores if valor is not None]
    if presentes and all(isinstance(valor, (int, float)) for valor in presentes):
        return "REAL"
    return "TEXT"


def verificar(entradas: Path, entradas_preparadas: Path, prep: Preparacion) -> list[str]:
    """Compara `entradas_preparadas/<destino>.csv` con lo que da la preparación.

    Devuelve las diferencias; una lista vacía quiere decir que coincide.
    """
    origen = leer_entradas(entradas).get(prep.origen.upper())
    if origen is None:
        return [f"falta el origen {prep.origen}.csv en entradas/"]
    calculada = aplicar(origen, prep)
    ruta = entradas_preparadas / f"{prep.destino}.csv"
    if not ruta.exists():
        return [f"falta el archivo {ruta.name}; genérelo con corpus_lib.generar_entradas_l2l3"]
    # Los reales se escriben con 12 cifras: la comparación es exacta salvo ese redondeo.
    return comparar_con_guardado(ruta, calculada, 1e-9, True)


def generar(entradas: Path, entradas_preparadas: Path, prep: Preparacion) -> Path:
    """Escribe `entradas_preparadas/<destino>.csv` a partir de las entradas del caso."""
    origen = leer_entradas(entradas)[prep.origen.upper()]
    ruta = entradas_preparadas / f"{prep.destino}.csv"
    escribir_csv(ruta, aplicar(origen, prep))
    return ruta
