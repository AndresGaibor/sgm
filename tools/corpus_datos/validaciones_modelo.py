"""Verdad plantada de los casos L8 de validaciones, en forma de filas tipadas.

Las filas salen del generador (`validaciones_filas.py`): cada una lleva su etiqueta de defecto.
Los tipos de columna siguen la convención del corpus (`csv_tabla.tipo_sql`), la que `DIFERENCIAS.md`
documenta para PROC IMPORT. El esperado se calcula a partir de estas filas y de su etiqueta, no del
SQL del programa; el cruce con el oráculo (`validaciones_cruce.py`) es lo que los compara.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_CARPETA = Path(__file__).resolve().parent
for _ruta in (_CARPETA.parent, _CARPETA):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

from corpus_lib.csv_tabla import Tabla, tipo_sql  # noqa: E402
from validaciones_filas import PRODUCTOS, fila_detalle, fila_ubicacion, secuencia  # noqa: E402


@dataclass(frozen=True)
class Fila:
    """Una fila de un CSV sin cabecera: etiqueta de defecto, texto crudo y valor tipado.

    Las claves son el número de variable (`VARn`, de 1 a 23 en el detalle; de 1 a 4 en ubicación).
    """

    producto: str
    etiqueta: str
    crudo: dict[int, str]
    valor: dict[int, object]

    def num(self, n: int) -> int | None:
        """Valor de `input(left(VARn), w.)` en el caso: entero, o faltante si el campo está vacío.

        Un texto no numérico (por ejemplo `XX`) también da faltante, como el informat de SAS.
        """
        texto = self.crudo[n].strip()
        if texto == "":
            return None
        try:
            return int(texto)
        except ValueError:
            return None


def _tipar(texto: str, tipo: str) -> object:
    if texto == "":
        return None
    if tipo == "INTEGER":
        return int(texto)
    if tipo == "REAL":
        return float(texto)
    return texto


def _tipos(crudos: list[list[str]]) -> list[str]:
    """Tipo SQL de cada columna según la convención del corpus (vacío es faltante)."""
    columnas = len(crudos[0]) if crudos else 0
    return [
        tipo_sql([None if fila[j] == "" else fila[j] for fila in crudos])
        for j in range(columnas)
    ]


def _armar(producto: str, pares: list[tuple[str, list[str]]]) -> list[Fila]:
    tipos = _tipos([campos for _, campos in pares])
    filas: list[Fila] = []
    for etiqueta, campos in pares:
        crudo = {j + 1: campos[j] for j in range(len(campos))}
        valor = {j + 1: _tipar(campos[j], tipos[j]) for j in range(len(campos))}
        filas.append(Fila(producto, etiqueta, crudo, valor))
    return filas


def detalle(spec: dict, producto: str) -> list[Fila]:
    """Filas del CSV de detalle de un producto, en el orden del archivo.

    En el caso v03 el detalle tiene una fila válida por cada llave de ubicación (`spec` trae
    `ubicacion`); en los demás, las etiquetas vienen de `spec["productos"]`.
    """
    info = PRODUCTOS[producto]
    if "productos" in spec:
        etiquetas = secuencia(spec["productos"][producto])
    else:
        etiquetas = ["validos"] * len(secuencia(spec["ubicacion"][producto]))
    pares = [(e, fila_detalle(e, i, info)) for i, e in enumerate(etiquetas)]
    return _armar(producto, pares)


def ubicacion(spec: dict, producto: str) -> list[Fila]:
    """Filas del CSV de ubicación (llave, país, código DANE, dirección) de un producto."""
    etiquetas = secuencia(spec["ubicacion"][producto])
    pares = [(e, fila_ubicacion(e, i)) for i, e in enumerate(etiquetas)]
    return _armar(producto, pares)


def excel_codigos(excel: dict, clave: str, columna: int = 0) -> set[str]:
    """Valores de una columna de un Excel de homologación, tal como los escribió el generador."""
    _, _, filas = excel[clave]
    return {fila[columna] for fila in filas}


def proyectar(fila: Fila, select: list[tuple[int, str]]) -> dict[str, object]:
    """Columnas de un SELECT: alias -> valor tipado, en el orden del programa."""
    return {alias: fila.valor[n] for n, alias in select}


def tabla(columnas: list[str], filas: list[dict[str, object]]) -> Tabla:
    """Tabla con las columnas en orden: cada fila es un diccionario alias -> valor."""
    return Tabla(list(columnas), [tuple(fila[c] for c in columnas) for fila in filas])


def conteos(clave: str, nombre: str, parejas: list[tuple[str, int]]) -> Tabla:
    """Tabla de conteos de los `OUTER UNION CORR` de un programa: una fila por producto.

    `clave` es el nombre de la primera columna (PRODUCTO, REGLA o ESTADO) y `nombre` el del conteo.
    """
    return Tabla([clave, nombre], [(etiqueta, n) for etiqueta, n in parejas])


@dataclass
class Esperado:
    """Salidas esperadas de un caso: tablas WORK (con cabecera) y archivos de PROC EXPORT."""

    tablas: dict[str, Tabla] = field(default_factory=dict)
    archivos: dict[str, Tabla] = field(default_factory=dict)


class IncoherenteConLaEtiqueta(ValueError):
    """La regla del programa, aplicada al contenido de la fila, no coincide con su etiqueta."""


def comprobar(fila: Fila, regla_programa: bool, decision: bool, motivo: str) -> None:
    """Exige que la etiqueta plantada y el contenido de la fila digan lo mismo.

    `regla_programa` es la condición del SQL aplicada al contenido; `decision` es la que sale de la
    etiqueta. Si no coinciden, el generador y el programa no hablan de la misma fila.
    """
    if regla_programa != decision:
        raise IncoherenteConLaEtiqueta(f"{fila.producto} '{fila.etiqueta}': {motivo}")
