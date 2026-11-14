"""Funciones numéricas SAS del oráculo, independientes del intérprete de producción."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable


def crear_funciones_numericas(faltante: object, es_faltante: Callable[[object], bool]) -> dict:
    """Crea el despacho numérico usando el centinela del oráculo llamador."""

    def numero(valor: object) -> float | None:
        if es_faltante(valor):
            return None
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"se esperaba un argumento numérico, llegó {type(valor).__name__}")
        return float(valor)

    def entero_cercano(valor: float) -> float:
        entero = round(valor)
        return float(entero) if abs(valor - entero) <= 1e-12 else valor

    def unary(funcion: Callable[[float], float]):
        def aplicar(valor: object) -> float | object:
            convertido = numero(valor)
            if convertido is None:
                return faltante
            try:
                resultado = funcion(convertido)
            except (ValueError, OverflowError):
                return faltante
            return resultado if math.isfinite(resultado) else faltante

        return aplicar

    def int_sas(valor: object) -> float | object:
        convertido = numero(valor)
        if convertido is None:
            return faltante
        return float(math.trunc(entero_cercano(convertido)))

    def ceil_sas(valor: object) -> float | object:
        convertido = numero(valor)
        return faltante if convertido is None else float(math.ceil(entero_cercano(convertido)))

    def floor_sas(valor: object) -> float | object:
        convertido = numero(valor)
        return faltante if convertido is None else float(math.floor(entero_cercano(convertido)))

    def mod_sas(dividendo: object, divisor: object) -> float | object:
        a, b = numero(dividendo), numero(divisor)
        if a is None or b is None or b == 0:
            return faltante
        try:
            resultado = math.fmod(a, b)
        except (ValueError, OverflowError):
            return faltante
        return resultado if math.isfinite(resultado) else faltante

    def round_sas(valor: object, unidad: object = 1) -> float | object:
        numero_valor, numero_unidad = numero(valor), numero(unidad)
        if numero_valor is None or numero_unidad is None or numero_unidad == 0:
            return faltante
        try:
            cociente = (
                Decimal(repr(numero_valor)) / Decimal(repr(numero_unidad))
            ).to_integral_value(rounding=ROUND_HALF_UP)
            resultado = float(cociente * Decimal(repr(numero_unidad)))
        except (ArithmeticError, ValueError, OverflowError):
            return faltante
        return resultado if math.isfinite(resultado) else faltante

    return {
        "int": int_sas,
        "ceil": ceil_sas,
        "floor": floor_sas,
        "mod": mod_sas,
        "abs": unary(abs),
        "sqrt": unary(math.sqrt),
        "log": unary(math.log),
        "exp": unary(math.exp),
        "sign": unary(lambda valor: float((valor > 0) - (valor < 0))),
        "round": round_sas,
    }
