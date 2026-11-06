"""Inferencia de tipos basada solo en las expresiones que aparecen en el programa."""

from __future__ import annotations

import re

from sgm.ir.models import Plan
from sgm.ir.types_code import expression_type

TIPO_POR_OMISION = "String"
TIPO_NUMERICO = "Double"
_CADENA = re.compile(r"'[^']*'|\"[^\"]*\"")
_PALABRAS = frozenset(
    {
        "and", "or", "not", "is", "null", "missing", "case", "when", "then", "else", "end",
        "true", "false", "between", "like", "in", "as", "distinct", "on", "select", "from",
        "where", "group", "order", "by", "having", "join", "left", "right", "inner", "outer",
        "desc", "asc", "work",
    }
)
_TOKEN = re.compile(
    r"'[^']*'|\"[^\"]*\""
    r"|(?P<ident>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)"
    r"|(?P<numero>\d+(?:\.\d+)?)"
    r"|(?P<operador>[+\-*/])"
    r"|(?P<otro>\S)"
)
_LLAMADA = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_SOLO_NOMBRE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?")
_FUNCIONES_NUMERICAS = frozenset(
    {
        "sum", "mean", "avg", "round", "abs", "int", "floor", "ceil", "sqrt", "exp",
        "log", "nmiss", "n", "min", "max",
    }
)
_FUNCIONES_MIXTAS = frozenset({"coalesce", "ifn"})


def _de_asignacion(asignacion: dict) -> list[str]:
    textos = [str(asignacion.get("expression") or "")]
    condicional = asignacion.get("conditional")
    if isinstance(condicional, dict):
        textos.extend(
            (str(condicional.get("condition") or ""), str(condicional.get("otherwise") or ""))
        )
        for rama in condicional.get("branches") or []:
            textos.extend((str(rama.get("condition") or ""), str(rama.get("expression") or "")))
    return textos


def _textos(plan: Plan) -> list[str]:
    """Expresiones que pueden demostrar el tipo de una columna."""
    encontrados: list[str] = []
    for op in plan.graph.operators():
        params = op.params
        if op.kind == "filter":
            encontrados.append(str(params.get("expression") or ""))
        for asignacion in params.get("assignments") or []:
            encontrados.extend(_de_asignacion(asignacion))
        for llave in params.get("keys") or []:
            encontrados.extend(str(parte) for parte in llave)
        if params.get("condition"):
            encontrados.append(str(params["condition"]))
        for paso in params.get("steps") or []:
            propios = paso.get("params") or {}
            if paso.get("kind") == "filter":
                encontrados.append(str(propios.get("expression") or ""))
            for asignacion in propios.get("assignments") or []:
                encontrados.extend(_de_asignacion(asignacion))
            for llave in propios.get("keys") or []:
                encontrados.extend(str(parte) for parte in llave)
            if propios.get("condition"):
                encontrados.append(str(propios["condition"]))
    return [texto for texto in encontrados if texto]


def _sin_tabla(nombre: str) -> str:
    return nombre.split(".")[-1].lower()


def _columnas_aritmeticas(texto: str) -> set[str]:
    piezas = [(m.lastgroup, m.group(0)) for m in _TOKEN.finditer(texto)]
    nombres: set[str] = set()
    for indice, (tipo, valor) in enumerate(piezas):
        if tipo != "operador":
            continue
        izquierda = piezas[indice - 1] if indice else (None, "")
        derecha = piezas[indice + 1] if indice + 1 < len(piezas) else (None, "")
        if valor in "*/":
            lados = (izquierda, derecha)
        elif izquierda[0] in ("ident", "numero") and derecha[0] in ("ident", "numero"):
            lados = (izquierda, derecha)
        else:
            continue
        nombres |= {_sin_tabla(lado) for lado_tipo, lado in lados if lado_tipo == "ident"}
    return {nombre for nombre in nombres if nombre not in _PALABRAS}


_NUMERO = r"-?\d+(?:\.\d+)?"
_NOMBRE = r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?"
_ORDEN_NUMERICO = re.compile(
    rf"\b({_NOMBRE})\s*(?:<=|>=|<|>)\s*{_NUMERO}\b"
    rf"|(?<![\w.]){_NUMERO}\s*(?:<=|>=|<|>)\s*({_NOMBRE})\b"
    rf"|\b({_NOMBRE})\s+BETWEEN\s+{_NUMERO}\s+AND\s+{_NUMERO}\b",
    re.IGNORECASE,
)


def _columnas_ordenadas(texto: str) -> set[str]:
    sin_cadenas = _CADENA.sub(" ", texto)
    nombres = {
        _sin_tabla(nombre)
        for encontrada in _ORDEN_NUMERICO.finditer(sin_cadenas)
        for nombre in encontrada.groups()
        if nombre
    }
    return {nombre for nombre in nombres if nombre not in _PALABRAS}


def _llamadas(texto: str) -> list[tuple[str, str]]:
    encontradas: list[tuple[str, str]] = []
    for coincidencia in _LLAMADA.finditer(texto):
        nivel = 0
        for posicion in range(coincidencia.end() - 1, len(texto)):
            if texto[posicion] == "(":
                nivel += 1
            elif texto[posicion] == ")":
                nivel -= 1
                if nivel == 0:
                    encontradas.append(
                        (coincidencia.group(1).lower(), texto[coincidencia.end() : posicion])
                    )
                    break
    return encontradas


def _nombres(texto: str) -> set[str]:
    limpio = _CADENA.sub(" ", texto)
    return {
        _sin_tabla(nombre)
        for nombre in re.findall(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?(?!\s*\()", limpio)
        if _sin_tabla(nombre) not in _PALABRAS
    }


def _es_numerica(texto: str) -> bool:
    piezas = [(m.lastgroup, m.group(0)) for m in _TOKEN.finditer(texto)]
    for indice, (tipo, valor) in enumerate(piezas):
        if tipo != "operador":
            continue
        izquierda = piezas[indice - 1] if indice else (None, "")
        derecha = piezas[indice + 1] if indice + 1 < len(piezas) else (None, "")
        if valor in "*/" or (
            izquierda[0] in ("ident", "numero") and derecha[0] in ("ident", "numero")
        ):
            return True
    return any(
        funcion in _FUNCIONES_NUMERICAS
        or (funcion in _FUNCIONES_MIXTAS and re.search(r"\d", _CADENA.sub(" ", argumentos)))
        for funcion, argumentos in _llamadas(texto)
    )


def tipo_de_expresion(texto: str) -> str | None:
    """Tipo demostrado por operadores o funciones, sin inferirlo del nombre de una columna."""
    limpio = texto.strip()
    if not limpio or _SOLO_NOMBRE.fullmatch(limpio):
        return None
    demostrado = expression_type(limpio)
    if demostrado is not None:
        return demostrado.type
    return TIPO_NUMERICO if _es_numerica(limpio) else TIPO_POR_OMISION


def _columnas_numericas(plan: Plan) -> set[str]:
    numericas: set[str] = set()
    for texto in _textos(plan):
        numericas |= _columnas_aritmeticas(texto)
        numericas |= _columnas_ordenadas(texto)
        for funcion, argumentos in _llamadas(texto):
            if funcion in _FUNCIONES_NUMERICAS or (
                funcion in _FUNCIONES_MIXTAS and re.search(r"\d", _CADENA.sub(" ", argumentos))
            ):
                numericas |= _nombres(argumentos)
    return numericas


__all__ = [
    "TIPO_NUMERICO",
    "TIPO_POR_OMISION",
    "_columnas_numericas",
    "_columnas_ordenadas",
    "_sin_tabla",
    "_textos",
    "tipo_de_expresion",
]
