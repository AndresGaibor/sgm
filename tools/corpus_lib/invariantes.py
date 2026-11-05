"""Invariantes de un caso: igualdades que deben cumplir sus salidas frente a sus entradas.

Gramática del texto en `caso.yaml`:

    relacion   := expresion ('==' | '<=' | '>=') expresion
    expresion  := termino (('+' | '-') termino)*
    termino    := número | filas(T) | suma(T.col) | valor(T.col)

T es el nombre de un CSV sin extensión. `filas` cuenta las filas de datos; `suma` suma las
celdas numéricas (las vacías no cuentan); `valor` toma la celda de la primera fila. Los nombres
se buscan en `esperado/`, luego en `entradas/` y luego en `entradas_preparadas/`. Las
comparaciones aceptan la tolerancia del caso.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

_SIMBOLOS = re.compile(r"==|<=|>=|\d+(?:\.\d+)?|[A-Za-z_]\w*|[()+\-.]")
_NUMERO_CELDA = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?$")
_FUNCIONES = frozenset({"filas", "suma", "valor"})
_OPERADORES = frozenset({"==", "<=", ">="})


class _Parser:
    """Analizador descendente de una relación. Cada nodo es una tupla: (tipo, ...)."""

    def __init__(self, texto: str) -> None:
        self.texto = texto
        simbolos = _SIMBOLOS.findall(texto)
        if "".join(simbolos) != re.sub(r"\s+", "", texto):
            raise ValueError("caracteres no reconocidos")
        self.simbolos = simbolos
        self.pos = 0

    def _ver(self) -> str | None:
        return self.simbolos[self.pos] if self.pos < len(self.simbolos) else None

    def _tomar(self, esperado: str | None = None) -> str:
        actual = self._ver()
        if actual is None:
            raise ValueError(f"la invariante '{self.texto}' termina antes de tiempo")
        if esperado is not None and actual != esperado:
            raise ValueError(f"se esperaba '{esperado}', no '{actual}'")
        self.pos += 1
        return actual

    def relacion(self) -> tuple[tuple, str, tuple]:
        izquierda = self._expresion()
        operador = self._ver()
        if operador not in _OPERADORES:
            raise ValueError(f"falta el operador (==, <= o >=) en '{self.texto}'")
        self.pos += 1
        derecha = self._expresion()
        if self._ver() is not None:
            raise ValueError(f"sobra texto al final de '{self.texto}'")
        return izquierda, operador, derecha

    def _expresion(self) -> tuple:
        nodo = self._termino()
        while self._ver() in ("+", "-"):
            operador = self._tomar()
            nodo = (operador, nodo, self._termino())
        return nodo

    def _termino(self) -> tuple:
        simbolo = self._tomar()
        if re.fullmatch(r"\d+(?:\.\d+)?", simbolo):
            return ("num", float(simbolo))
        if simbolo not in _FUNCIONES:
            raise ValueError(f"se esperaba un número o filas, suma o valor, no '{simbolo}'")
        self._tomar("(")
        tabla = self._nombre()
        if simbolo == "filas":
            self._tomar(")")
            return ("filas", tabla)
        self._tomar(".")
        columna = self._nombre()
        self._tomar(")")
        return (simbolo, tabla, columna)

    def _nombre(self) -> str:
        simbolo = self._tomar()
        if not re.fullmatch(r"[A-Za-z_]\w*", simbolo):
            raise ValueError(f"se esperaba un nombre, no '{simbolo}'")
        return simbolo


def analizar(texto: str) -> tuple[tuple, str, tuple]:
    """Convierte el texto de una invariante en su árbol. Lanza ValueError si no es válido."""
    return _Parser(texto).relacion()


def _tabla(nombre: str, carpetas: list[Path]) -> tuple[list[str], list[list[str]]]:
    for carpeta in carpetas:
        ruta = carpeta / f"{nombre}.csv"
        if ruta.is_file():
            with ruta.open(encoding="utf-8-sig", newline="") as archivo:
                filas = list(csv.reader(archivo))
            return (filas[0] if filas else []), filas[1:]
    raise ValueError(f"no existe la tabla '{nombre}' en las carpetas del caso")


def _numero(celda: str, nombre: str) -> float:
    if not _NUMERO_CELDA.match(celda):
        raise ValueError(f"la celda '{celda}' de {nombre} no es numérica")
    return float(celda)


def _indice(columnas: list[str], nombre: str, tabla: str) -> int:
    if nombre not in columnas:
        raise ValueError(f"la tabla {tabla} no tiene la columna '{nombre}'")
    return columnas.index(nombre)


def _evaluar(nodo: tuple, carpetas: list[Path]) -> float:
    tipo = nodo[0]
    if tipo == "num":
        return nodo[1]
    if tipo in ("+", "-"):
        izquierda = _evaluar(nodo[1], carpetas)
        derecha = _evaluar(nodo[2], carpetas)
        return izquierda + derecha if tipo == "+" else izquierda - derecha
    if tipo == "filas":
        return float(len(_tabla(nodo[1], carpetas)[1]))
    columnas, filas = _tabla(nodo[1], carpetas)
    indice = _indice(columnas, nodo[2], nodo[1])
    celdas = [fila[indice] for fila in filas]
    if tipo == "suma":
        return sum(_numero(c, f"{nodo[1]}.{nodo[2]}") for c in celdas if c != "")
    if not celdas:
        raise ValueError(f"{nodo[1]} no tiene filas para tomar valor")
    if celdas[0] == "":
        raise ValueError(f"la primera celda de {nodo[1]}.{nodo[2]} está vacía")
    return _numero(celdas[0], f"{nodo[1]}.{nodo[2]}")


def _mensaje(texto: str, izquierda: float, operador: str, derecha: float) -> str:
    return f"no se cumple: {texto} ({izquierda:g} {operador} {derecha:g})"


def comprobar(invariantes: list[str], carpetas: list[Path], tolerancia: float) -> list[str]:
    """Evalúa cada invariante. Devuelve las que no se cumplen o no se pueden evaluar."""
    fallos: list[str] = []
    for texto in invariantes:
        try:
            izquierda_nodo, operador, derecha_nodo = analizar(texto)
            izquierda = _evaluar(izquierda_nodo, carpetas)
            derecha = _evaluar(derecha_nodo, carpetas)
        except ValueError as error:
            fallos.append(f"no se pudo evaluar: {texto} ({error})")
            continue
        margen = tolerancia + 1e-9
        if operador == "==":
            cumple = abs(izquierda - derecha) <= margen
        elif operador == "<=":
            cumple = izquierda <= derecha + margen
        else:
            cumple = izquierda + margen >= derecha
        if not cumple:
            fallos.append(_mensaje(texto, izquierda, operador, derecha))
    return fallos
