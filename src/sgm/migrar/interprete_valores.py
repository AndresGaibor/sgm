"""Valores de las expresiones del intérprete: columnas, funciones SAS y aritmética (B-11 a B-14).

Movido desde `interprete.py` sin cambiar comportamiento (decisión del dueño, hito 241m).
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from sgm.migrar import semantica
from sgm.migrar.interprete_base import NoSoportadoEnInterprete, _numero
from sgm.migrar.interprete_funciones import _funcion

_FUNCIONES_SAS = re.compile(r"(?i)\b(input|left|substrn|substr|coalescec|compress|scan)\s*(?=\()")


# -- valores ------------------------------------------------------------------------------------
def _tabla(nombre: object) -> str:
    """`WORK.ventas` a `ventas`: el intérprete no distingue bibliotecas."""
    return str(nombre or "").strip().lower().split(".")[-1]


def _primero(params: dict, clave: str) -> str:
    valores = params.get(clave) or [""]
    return str(valores[0])


def _arbol(expresion: str):
    """Árbol de una expresión SQL; lo que no se puede leer no se adivina."""
    try:
        preparada = _FUNCIONES_SAS.sub(lambda m: f"sgm_{m.group(1).lower()}", expresion)
        return sqlglot.parse_one(preparada)
    except ParseError as error:
        raise NoSoportadoEnInterprete("expresion", f"'{expresion}': {error}") from None


def _verdad(valor: object) -> bool:
    """True si la expresión no es cero ni faltante (`lestmtsref`, p. 130)."""
    if isinstance(valor, bool):
        return valor
    numero = _numero(valor)
    return numero is not None and numero != 0


def _patron(patron: str) -> re.Pattern[str]:
    """`LIKE` de SQL: `%` cualquier secuencia, `_` un carácter; el resto, literal."""
    partes = ["^"]
    for caracter in patron:
        if caracter == "%":
            partes.append(".*")
        elif caracter == "_":
            partes.append(".")
        else:
            partes.append(re.escape(caracter))
    partes.append("$")
    return re.compile("".join(partes), re.DOTALL)


def _aritmetica(operador: str, izquierda: object, derecha: object) -> object:
    """Suma, resta, producto y división: con un faltante o texto no numérico, el resultado falta."""
    uno, otro = _numero(izquierda), _numero(derecha)
    if uno is None or otro is None:
        return None
    if operador == "+":
        return uno + otro
    if operador == "-":
        return uno - otro
    if operador == "*":
        return uno * otro
    if otro == 0:
        return None  # en SAS dividir por cero da faltante
    return uno / otro


def _columna(fila: dict, nombre: str) -> object:
    """Valor de una columna sin distinguir mayúsculas: `DESCRIPCION` y `descripcion` son iguales."""
    if nombre in fila:
        return fila[nombre]
    buscado = nombre.lower()
    for clave, valor in fila.items():
        if str(clave).lower() == buscado:
            return valor
    return None


def _valor(nodo, fila: dict) -> object:
    """Valor de un nodo del árbol sobre una fila. Lo que no entiende, lo dice."""
    if isinstance(nodo, exp.Paren):
        return _valor(nodo.this, fila)
    if isinstance(nodo, exp.Column):
        if nodo.table and nodo.table.lower() in ("first", "last"):
            # `FIRST.v` y `LAST.v` del DATA step: las pone `_por_grupo` en la fila como `first.v`.
            return _columna(fila, f"{nodo.table}.{nodo.name}".lower())
        return _columna(fila, nodo.name)
    if isinstance(nodo, exp.Literal):
        return nodo.this if nodo.is_string else _numero(nodo.this)
    if isinstance(nodo, exp.Boolean):
        return bool(nodo.this)
    if isinstance(nodo, exp.Null):
        return None
    if isinstance(nodo, exp.Neg):
        valor = _numero(_valor(nodo.this, fila))
        return None if valor is None else -valor
    if isinstance(nodo, exp.Round):
        valor = _numero(_valor(nodo.this, fila))
        precision = nodo.args.get("decimals")
        multiplo = _numero(_valor(precision, fila)) if precision is not None else 1
        if valor is None or multiplo in (None, 0):
            return None
        cociente = Decimal(str(valor)) / Decimal(str(multiplo))
        redondeado = cociente.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return float(redondeado * Decimal(str(multiplo)))
    if isinstance(nodo, exp.Cast):
        return _valor(nodo.this, fila)
    if isinstance(nodo, exp.And):
        return _verdad(_valor(nodo.this, fila)) and _verdad(_valor(nodo.expression, fila))
    if isinstance(nodo, exp.Or):
        return _verdad(_valor(nodo.this, fila)) or _verdad(_valor(nodo.expression, fila))
    if isinstance(nodo, exp.Not):
        return not _verdad(_valor(nodo.this, fila))
    if isinstance(nodo, exp.EQ):
        return semantica.iguales(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.NEQ):
        return semantica.distintos(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.LT):
        return semantica.menor(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.LTE):
        return semantica.menor_igual(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.GT):
        return semantica.mayor(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.GTE):
        return semantica.mayor_igual(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.Is):
        nulo = isinstance(nodo.expression, exp.Null)
        return semantica.es_faltante(_valor(nodo.this, fila)) is nulo
    if isinstance(nodo, exp.Like):
        texto = semantica.como_texto(_valor(nodo.this, fila))
        patron = semantica.como_texto(_valor(nodo.expression, fila))
        return _patron(patron).match(texto) is not None
    if isinstance(nodo, exp.In):
        if nodo.args.get("query") is not None:
            raise NoSoportadoEnInterprete("subconsulta", "IN con SELECT")
        buscado = _valor(nodo.this, fila)
        return any(
            semantica.iguales(buscado, _valor(opcion, fila)) for opcion in nodo.expressions
        )
    if isinstance(nodo, exp.Between):
        valor = _valor(nodo.this, fila)
        bajo = _valor(nodo.args["low"], fila)
        alto = _valor(nodo.args["high"], fila)
        return semantica.mayor_igual(valor, bajo) and semantica.menor_igual(valor, alto)
    if isinstance(nodo, exp.Case):
        for rama in nodo.args.get("ifs") or []:
            if _verdad(_valor(rama.this, fila)):
                return _valor(rama.args["true"], fila)
        por_omision = nodo.args.get("default")
        return None if por_omision is None else _valor(por_omision, fila)
    if isinstance(nodo, (exp.Add, exp.Sub, exp.Mul, exp.Div)):
        simbolo = {exp.Add: "+", exp.Sub: "-", exp.Mul: "*", exp.Div: "/"}[type(nodo)]
        return _aritmetica(simbolo, _valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, (exp.DPipe, exp.Concat)):
        izquierda = semantica.como_texto(_valor(nodo.this, fila))
        derecha = semantica.como_texto(_valor(nodo.expression, fila))
        return izquierda + derecha
    if isinstance(nodo, exp.Trim):
        return semantica.como_texto(_valor(nodo.this, fila)).rstrip()
    if isinstance(nodo, exp.Coalesce):
        # En sqlglot el primer argumento va en `this`, no en `expressions`.
        argumentos = [nodo.this, *nodo.expressions]
        return _funcion("coalesce", [_valor(arg, fila) for arg in argumentos])
    if isinstance(nodo, exp.Upper):
        return semantica.como_texto(_valor(nodo.this, fila)).upper()
    if isinstance(nodo, exp.Lower):
        return semantica.como_texto(_valor(nodo.this, fila)).lower()
    if isinstance(nodo, exp.Anonymous):
        return _funcion(nodo.name.lower(), [_valor(arg, fila) for arg in nodo.expressions])
    raise NoSoportadoEnInterprete("expresion", f"{type(nodo).__name__}: {nodo.sql()}")


# -- filas --------------------------------------------------------------------------------------
