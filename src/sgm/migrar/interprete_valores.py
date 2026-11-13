"""Valores de las expresiones del intérprete: columnas, funciones SAS y aritmética (B-11 a B-14).

Movido desde `interprete.py` sin cambiar comportamiento (decisión del dueño, hito 241m).
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from sgm.migrar import semantica

_FUNCIONES_SAS = re.compile(r"(?i)\b(input|left|substrn|substr|coalescec|compress|scan)\s*(?=\()")


class NoSoportadoEnInterprete(RuntimeError):
    """El plan usa algo que el intérprete no sabe ejecutar; se dice qué, no se salta."""

    def __init__(self, kind: str, detalle: str = "") -> None:
        self.kind = kind
        self.detalle = detalle
        super().__init__(f"{kind}: {detalle}" if detalle else kind)


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


def _numero(valor: object) -> float | None:
    return semantica.como_numero(valor)


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


def _funcion(nombre: str, argumentos: list) -> object:
    if nombre.startswith("sgm_"):
        nombre = nombre[4:]
    if nombre.startswith("row_"):
        nombre = nombre[4:]
    if nombre == "mean":
        valores = [_numero(valor) for valor in argumentos]
        presentes = [valor for valor in valores if valor is not None]
        return sum(presentes) / len(presentes) if presentes else None
    if nombre in ("min", "max"):
        valores = [_numero(valor) for valor in argumentos]
        presentes = [valor for valor in valores if valor is not None]
        return (min(presentes) if nombre == "min" else max(presentes)) if presentes else None
    if nombre == "missing":
        return semantica.es_faltante(argumentos[0] if argumentos else None)
    if nombre == "coalesce":
        return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)
    if nombre == "coalescec":
        return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)
    if nombre == "trim":
        return semantica.como_texto(argumentos[0] if argumentos else None).rstrip()
    if nombre == "strip":
        return semantica.como_texto(argumentos[0] if argumentos else None).strip()
    if nombre == "upcase":
        return semantica.como_texto(argumentos[0] if argumentos else None).upper()
    if nombre == "lowcase":
        return semantica.como_texto(argumentos[0] if argumentos else None).lower()
    if nombre == "length":
        return len(semantica.como_texto(argumentos[0] if argumentos else None))
    if nombre == "left":
        texto = semantica.como_texto(argumentos[0] if argumentos else None)
        return texto.lstrip(" ") + " " * (len(texto) - len(texto.lstrip(" ")))
    if nombre in ("substr", "substrn"):
        if len(argumentos) < 2 or semantica.es_faltante(argumentos[0]):
            return " "
        texto = _texto_substr(argumentos[0], nombre)
        inicio = int(_numero(argumentos[1]) or 1) - 1
        longitud = (
            None
            if len(argumentos) < 3 or semantica.es_faltante(argumentos[2])
            else int(_numero(argumentos[2]) or 0)
        )
        if inicio < 0:
            inicio = max(len(texto) + inicio, 0)
        return texto[inicio:] if longitud is None else texto[inicio : inicio + max(longitud, 0)]
    if nombre == "input":
        return _input_wd(argumentos)
    if nombre == "compress":
        return _compress(argumentos)
    if nombre == "scan":
        return _scan(argumentos)
    if nombre == "abs":
        numero = _numero(argumentos[0] if argumentos else None)
        return None if numero is None else abs(numero)
    if nombre == "sum":
        valores = [_numero(valor) for valor in argumentos]
        if any(not semantica.es_faltante(valor) and convertido is None
               for valor, convertido in zip(argumentos, valores, strict=True)):
            raise NoSoportadoEnInterprete("funcion", "SUM requiere argumentos numéricos")
        presentes = [valor for valor in valores if valor is not None]
        return sum(presentes) if presentes else None
    raise NoSoportadoEnInterprete("funcion", nombre)


def _texto_substr(valor: object, funcion: str) -> str:
    """Conversión numérica documentada para SUBSTR/SUBSTRN en las expresiones del corpus."""
    if isinstance(valor, (int, float)):
        texto = format(valor, ".12g")
        return texto if funcion == "substrn" else texto.rjust(12)
    return semantica.como_texto(valor)


def _input_wd(argumentos: list) -> float | None:
    """Subconjunto documentado INPUT(x,w.d): convierte números y aplica d solo sin punto decimal."""
    if len(argumentos) < 2:
        raise NoSoportadoEnInterprete("funcion", "INPUT requiere el valor y un informat w.d")
    texto = semantica.como_texto(argumentos[0]).strip()
    informat = _numero(argumentos[1])
    if not texto or texto == "." or informat is None:
        return None
    decimales = int(round((informat - int(informat)) * 10))
    try:
        if "." in texto:
            return float(texto)
        numero = Decimal(texto) / (Decimal(10) ** decimales)
        return float(numero)
    except (InvalidOperation, ValueError):
        return None


def _compress(argumentos: list) -> str:
    """COMPRESS con lista de caracteres y modificadores usados por los vectores documentados."""
    texto = semantica.como_texto(argumentos[0] if argumentos else None)
    lista = semantica.como_texto(argumentos[1]) if len(argumentos) > 1 else " "
    modificadores = semantica.como_texto(argumentos[2]).lower() if len(argumentos) > 2 else ""
    quitar: set[str] = set(lista)
    if "d" in modificadores:
        quitar.update("0123456789")
    if "a" in modificadores:
        quitar.update("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "l" in modificadores:
        quitar.update("abcdefghijklmnopqrstuvwxyz")
    if "u" in modificadores:
        quitar.update("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "s" in modificadores:
        quitar.update(" \t\n\r\f\v")
    if "i" in modificadores:
        quitar.update(caracter.lower() for caracter in tuple(quitar))
        quitar.update(caracter.upper() for caracter in tuple(quitar))
    if "k" in modificadores:
        return "".join(caracter for caracter in texto if caracter in quitar)
    return "".join(caracter for caracter in texto if caracter not in quitar)


def _scan(argumentos: list) -> str:
    """SCAN con delimitadores explícitos y blancos por omisión, según vectores del corpus."""
    if len(argumentos) < 2:
        return " "
    texto = semantica.como_texto(argumentos[0])
    posicion = int(_numero(argumentos[1]) or 0)
    delimitadores = (
        semantica.como_texto(argumentos[2])
        if len(argumentos) > 2
        else " \t\n\r!$%&()*+,-./;<^|"
    )
    if not delimitadores:
        delimitadores = " \t\n\r!$%&()*+,-./;<^|"
    patron = "[" + re.escape(delimitadores) + "]+"
    tokens = [token for token in re.split(patron, texto) if token]
    indice = posicion - 1 if posicion > 0 else len(tokens) + posicion
    return tokens[indice] if 0 <= indice < len(tokens) else " "


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
