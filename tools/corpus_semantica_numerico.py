"""Funciones numéricas SAS del oráculo, independientes del intérprete de producción."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable


def crear_funciones_numericas(faltante: object, es_faltante: Callable[[object], bool]) -> dict:
    """Crea el despacho numérico usando el centinela del oráculo llamador."""

    def falta_sas(valor: object) -> bool:
        return valor.strip(" ") == "" if isinstance(valor, str) else es_faltante(valor)

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

    def numeros(argumentos: tuple[object, ...]) -> list[float | None]:
        if not argumentos:
            raise TypeError("la función requiere al menos un argumento numérico")
        return [numero(valor) for valor in argumentos]

    def agregacion(nombre: str, funcion: Callable[[list[float]], float]):
        def aplicar(*argumentos: object) -> float | object:
            valores = [valor for valor in numeros(argumentos) if valor is not None]
            return funcion(valores) if valores else faltante

        return aplicar

    def n(*argumentos: object) -> int:
        return sum(valor is not None for valor in numeros(argumentos))

    def nmiss(*argumentos: object) -> int:
        return sum(valor is None for valor in numeros(argumentos))

    def cmiss(*argumentos: object) -> int:
        if not argumentos:
            raise TypeError("CMISS requiere argumentos")
        return sum(falta_sas(valor) for valor in argumentos)

    def coalesce(*argumentos: object) -> object:
        for original, convertido in zip(argumentos, numeros(argumentos), strict=True):
            if convertido is not None:
                return original
        return faltante

    def ifn(*argumentos: object) -> object:
        if len(argumentos) not in (3, 4):
            raise TypeError("IFN requiere tres o cuatro argumentos")
        condicion = numero(argumentos[0])
        indice = 1 if condicion is not None and condicion != 0 else 2
        if condicion is None and len(argumentos) == 4:
            indice = 3
        elegido = argumentos[indice]
        valor = numero(elegido)
        return faltante if valor is None else valor

    def ifc(*argumentos: object) -> object:
        if len(argumentos) not in (3, 4):
            raise TypeError("IFC requiere tres o cuatro argumentos")
        condicion = numero(argumentos[0])
        indice = 1 if condicion is not None and condicion != 0 else 2
        if condicion is None and len(argumentos) == 4:
            indice = 3
        elegido = argumentos[indice]
        if falta_sas(elegido):
            return faltante
        if not isinstance(elegido, str):
            raise TypeError("IFC requiere valores de texto")
        return elegido

    def missing(valor: object) -> bool:
        return falta_sas(valor)

    return {
        "sum": agregacion("SUM", sum),
        "mean": agregacion("MEAN", lambda valores: sum(valores) / len(valores)),
        "min": agregacion("MIN", min),
        "max": agregacion("MAX", max),
        "n": n,
        "nmiss": nmiss,
        "cmiss": cmiss,
        "coalesce": coalesce,
        "ifn": ifn,
        "ifc": ifc,
        "missing": missing,
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
