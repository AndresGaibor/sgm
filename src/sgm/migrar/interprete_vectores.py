"""Adaptadores entre la forma de los vectores y las expresiones del intérprete."""

from __future__ import annotations

import math

from . import semantica
from .interprete import _arbol, _aritmetica, _valor
from .interprete_funciones import llamar
from .interprete_operadores import entre, parecido, pertenece

FUNCIONES_VECTOR = frozenset(
    {"between", "cmp", "concat", "in", "is_missing", "like", "round", "suma_mas", "trim_concat"}
)
_COMPARADORES = {
    "=": lambda resultado: resultado == 0,
    "<": lambda resultado: resultado < 0,
    "<=": lambda resultado: resultado <= 0,
    ">": lambda resultado: resultado > 0,
    ">=": lambda resultado: resultado >= 0,
    "^=": lambda resultado: resultado != 0,
}


def _literal_sql(valor: object) -> str:
    """Codifica un valor escalar como literal SQL, sin interpretar texto como código."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, str):
        return "'" + valor.replace("'", "''") + "'"
    if isinstance(valor, (int, float)):
        if isinstance(valor, float) and not math.isfinite(valor):
            raise ValueError("el vector no puede contener un número no finito")
        return repr(valor)
    raise TypeError(f"tipo de literal no admitido en un vector: {type(valor).__name__}")


def _evaluar_expresion(expresion: str) -> object:
    return _valor(_arbol(expresion), {})


def evaluar_vector(funcion: str, entrada: list) -> object:
    """Ejecuta con el intérprete y adapta los argumentos propios del oráculo de vectores."""
    nombre = funcion.strip().lower()
    if nombre == "input":
        if len(entrada) != 3:
            raise ValueError("el vector INPUT debe contener campo, ancho y decimales")
        ancho = semantica.como_numero(entrada[1])
        decimales = semantica.como_numero(entrada[2])
        if (
            ancho is None
            or decimales is None
            or not ancho.is_integer()
            or not decimales.is_integer()
        ):
            raise ValueError("el vector INPUT requiere ancho y decimales enteros")
        return llamar("input", [entrada[0], f"{int(ancho)}.{int(decimales)}"])
    if nombre == "cmp":
        if len(entrada) != 3 or entrada[1] not in _COMPARADORES:
            raise ValueError("el vector CMP requiere dos valores y un operador documentado")
        return _COMPARADORES[entrada[1]](semantica.comparar(entrada[0], entrada[2]))
    if nombre == "in":
        if len(entrada) != 2 or not isinstance(entrada[1], list):
            raise ValueError("el vector IN requiere un valor y una lista")
        return pertenece(entrada[0], entrada[1])
    if nombre == "between":
        if len(entrada) != 3:
            raise ValueError("el vector BETWEEN requiere valor y dos límites")
        return entre(*entrada)
    if nombre == "like":
        if len(entrada) != 2:
            raise ValueError("el vector LIKE requiere texto y patrón")
        return parecido(*entrada)
    if nombre == "suma_mas":
        if len(entrada) != 2:
            raise ValueError("el vector SUMA_MAS requiere dos operandos")
        return _aritmetica("+", entrada[0], entrada[1])
    if nombre == "is_missing":
        if len(entrada) != 1:
            raise ValueError("el vector IS MISSING requiere un valor")
        return semantica.es_faltante(entrada[0])
    if nombre == "concat":
        if not entrada:
            return ""
        expresion = " || ".join(_literal_sql(valor) for valor in entrada)
        return _evaluar_expresion(expresion)
    if nombre == "trim_concat":
        if len(entrada) != 2:
            raise ValueError("el vector TRIM_CONCAT requiere dos valores")
        expresion = f"TRIM({_literal_sql(entrada[0])}) || {_literal_sql(entrada[1])}"
        return _evaluar_expresion(expresion)
    if nombre == "round":
        expresion = f"ROUND({', '.join(_literal_sql(valor) for valor in entrada)})"
        return _evaluar_expresion(expresion)
    return llamar(nombre, entrada)
