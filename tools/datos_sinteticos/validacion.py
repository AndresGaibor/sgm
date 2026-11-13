"""Validación compartida de valores según el tipo demostrado."""

import math
import re

_NUMERO = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
_ENTERO = re.compile(r"[+-]?\d+\Z")


def validar_valor(valor: str, tipo: str | None) -> str:
    """Comprueba sintaxis y rango sin inferir ni modificar el valor."""
    if not isinstance(valor, str) or "\x00" in valor:
        raise ValueError("valor inválido")
    if tipo in {"Integer", "Long"}:
        if not _ENTERO.fullmatch(valor):
            raise ValueError("entero inválido")
        entero = int(valor)
        limite = 2 ** (31 if tipo == "Integer" else 63)
        if not -limite <= entero < limite:
            raise ValueError("entero fuera de rango")
    elif tipo == "Double":
        if not _NUMERO.fullmatch(valor) or not math.isfinite(float(valor)):
            raise ValueError("decimal inválido")
    return valor


def validar_columnas(nombres: list[str]) -> None:
    """Rechaza esquemas vacíos o ambiguos sin distinguir mayúsculas."""
    if not nombres or len({nombre.casefold() for nombre in nombres}) != len(nombres):
        raise ValueError("esquema vacío o con columnas duplicadas")
