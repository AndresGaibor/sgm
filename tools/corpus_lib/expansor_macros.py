"""Expansor mínimo de macros SAS para los casos L5: produce el programa sin macros.

Soporta: `%let nombre = valor;`, `%macro nombre(p1, p2); ... %mend;` con parámetros posicionales,
llamadas `%nombre(a, b);`, `%if cond %then ... %else ...;` con `%do; ... %end;`, `%do i=a %to b;`,
`&var` y `&var.` (el punto final se consume), `%eval(expr)` con enteros y `+ - *`,
`%str(texto)` (sin resolver), `%sysfunc(f(args))` con las funciones de
`corpus_semantica_funciones`, `%put ...;` (se quita) y `SELECT ... INTO :var FROM ...;`, que se
quita y asigna `var` con el valor que el llamador saca de la primera fila (ver
https://support.sas.com/documentation/cdl/en/sqlproc/63043/HTML/default/n1tupenuhmu1j0n19d3curl9igt4.htm).

Como en SAS, no se resuelven macros dentro de cadenas con comilla simple ni dentro de
comentarios `/* */`. Dentro de comillas dobles sí. Cualquier construcción fuera de esta lista
falla con `ErrorMacro`: no se expande en silencio.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from corpus_semantica_funciones import FUNCIONES, evaluar

from .expansor_util import ErrorMacro, _argumento, _entero_seguro, _partir

__all__ = ["ErrorMacro", "expandir"]

_LET = re.compile(r"%let\s+(\w+)\s*=", re.IGNORECASE)
_MACRO = re.compile(r"%macro\s+(\w+)\s*(?:\(([^)]*)\))?\s*;", re.IGNORECASE)
_MEND = re.compile(r"%mend\b[^;]*;", re.IGNORECASE)
_IF = re.compile(r"%if\b(.*?)%then\b", re.IGNORECASE | re.DOTALL)
_COMPARACION = re.compile(r"^(.*?)\s*(\^=|~=|<>|=)\s*(.*)$", re.DOTALL)
_ELSE = re.compile(r"\s*%else\b", re.IGNORECASE)
_DO_SIMPLE = re.compile(r"%do\s*;", re.IGNORECASE)
_DO_LOOP = re.compile(r"%do\s+(\w+)\s*=\s*(.+?)\s+%to\s+(.+?)\s*;", re.IGNORECASE)
_BLOQUE = re.compile(r"%(do|end)\b", re.IGNORECASE)
_AMPERSAND = re.compile(r"&(\w+)\.?")
_FUNCION_MACRO = re.compile(r"%(eval|sysfunc|str)\(", re.IGNORECASE)
_PUT = re.compile(r"%put\b[^;]*;", re.IGNORECASE)
_LLAMADA = re.compile(r"%(\w+)", re.IGNORECASE)
_SELECT_INTO = re.compile(r"SELECT\b[^;]*?\bINTO\s*:\s*(\w+)[^;]*;", re.IGNORECASE)
_ENTERO_EXPR = re.compile(r"^[\d\s+\-*()]+$")
_CALL_FUNC = re.compile(r"^(\w+)\((.*)\)$", re.DOTALL)


@dataclass
class _Estado:
    """Lo que el expansor recuerda entre sentencias: macros definidas y valores de INTO."""

    into: dict[str, str]
    macros: dict[str, tuple[list[str], str]] = field(default_factory=dict)


def expandir(texto: str, into: dict[str, str] | None = None) -> str:
    """Devuelve el programa con las macros expandidas. `into` da el valor de cada `INTO :var`."""
    return _procesar(texto, {}, _Estado(into=dict(into or {})))


def _procesar(texto: str, ambito: dict[str, str], est: _Estado) -> str:
    salida: list[str] = []
    i = 0
    while i < len(texto):
        c = texto[i]
        if texto.startswith("/*", i):
            fin = texto.find("*/", i + 2)
            fin = len(texto) - 2 if fin < 0 else fin
            salida.append(texto[i : fin + 2])
            i = fin + 2
        elif c == "'":
            fin = _cierre(texto, i)
            salida.append(texto[i : fin + 1])
            i = fin + 1
        elif c == '"':
            fin = _cierre(texto, i)
            interior = _procesar(texto[i + 1 : fin], ambito, est)
            salida.append('"' + interior + '"')
            i = fin + 1
        elif c == "&":
            m = _AMPERSAND.match(texto, i)
            if not m:
                salida.append(c)
                i += 1
                continue
            salida.append(_valor(ambito, m.group(1)))
            i = m.end()
        elif c == "%":
            i, texto_nuevo = _macro(texto, i, ambito, est)
            salida.append(texto_nuevo)
        elif _empieza_select(texto, i):
            m = _SELECT_INTO.match(texto, i)
            if m:
                ambito[m.group(1)] = _valor(est.into, m.group(1))
                i = m.end()
            else:
                salida.append(c)
                i += 1
        else:
            salida.append(c)
            i += 1
    return "".join(salida)


def _empieza_select(texto: str, i: int) -> bool:
    if texto[i : i + 6].upper() != "SELECT":
        return False
    return i == 0 or not (texto[i - 1].isalnum() or texto[i - 1] == "_")


def _valor(datos: dict[str, str], nombre: str) -> str:
    if nombre not in datos:
        raise ErrorMacro(f"macrovariable no definida: &{nombre}")
    return datos[nombre]


def _cierre(texto: str, inicio: int) -> int:
    """Posición de la comilla que cierra la cadena que empieza en `inicio`."""
    comilla = texto[inicio]
    j = inicio + 1
    while j < len(texto):
        if texto[j] == comilla:
            if j + 1 < len(texto) and texto[j + 1] == comilla:
                j += 2
                continue
            return j
        j += 1
    raise ErrorMacro("cadena sin cerrar")


def _parentesis(texto: str, pos: int) -> tuple[str, int]:
    """Si `texto[pos]` es '(', devuelve el contenido y la posición después del ')' que cierra."""
    profundidad = 0
    for j in range(pos, len(texto)):
        if texto[j] == "(":
            profundidad += 1
        elif texto[j] == ")":
            profundidad -= 1
            if profundidad == 0:
                return texto[pos + 1 : j], j + 1
    raise ErrorMacro("paréntesis sin cerrar en una llamada de macro")


def _macro(texto: str, i: int, ambito: dict[str, str], est: _Estado) -> tuple[int, str]:
    """Procesa la construcción de macro que empieza en `i`. Devuelve posición nueva y texto."""
    m = _LET.match(texto, i)
    if m:
        fin = _punto_y_coma(texto, m.end())
        ambito[m.group(1)] = _procesar(texto[m.end() : fin], ambito, est).strip()
        return fin + 1, ""
    m = _MACRO.match(texto, i)
    if m:
        fin = _MEND.search(texto, m.end())
        if fin is None:
            raise ErrorMacro(f"%macro {m.group(1)} sin %mend")
        parametros = [p.strip() for p in (m.group(2) or "").split(",") if p.strip()]
        est.macros[m.group(1)] = (parametros, texto[m.end() : fin.start()])
        return fin.end(), ""
    m = _PUT.match(texto, i)
    if m:
        return m.end(), ""
    m = _IF.match(texto, i)
    if m:
        return _si(texto, i, m, ambito, est)
    m = _DO_LOOP.match(texto, i)
    if m:
        return _bucle(texto, m, ambito, est)
    if _DO_SIMPLE.match(texto, i):
        inicio = _DO_SIMPLE.match(texto, i).end()
        fin = _cierre_do(texto, inicio)
        siguiente = _punto_y_coma(texto, fin) + 1
        return siguiente, _procesar(texto[inicio:fin], ambito, est)
    m = _FUNCION_MACRO.match(texto, i)
    if m:
        interior, siguiente = _parentesis(texto, m.end() - 1)
        return siguiente, _funcion_macro(m.group(1).lower(), interior, ambito, est)
    m = _LLAMADA.match(texto, i)
    if m and m.group(1) in est.macros:
        return _llamar(texto, m, ambito, est)
    raise ErrorMacro(f"construcción de macro no soportada: {texto[i : i + 30]!r}")


def _punto_y_coma(texto: str, desde: int) -> int:
    fin = texto.find(";", desde)
    if fin < 0:
        raise ErrorMacro("sentencia de macro sin ';'")
    return fin


def _cierre_do(texto: str, inicio: int) -> int:
    """Posición del `%end` que cierra el `%do` cuyo cuerpo empieza en `inicio`."""
    profundidad = 1
    for m in _BLOQUE.finditer(texto, inicio):
        profundidad += 1 if m.group(1).lower() == "do" else -1
        if profundidad == 0:
            return m.start()
    raise ErrorMacro("%do sin %end")


def _rama(texto: str, pos: int, ambito: dict[str, str], est: _Estado) -> tuple[str, int]:
    """Lee una rama de %then o %else: un %do;...%end; o una sentencia. Devuelve (texto, fin)."""
    while pos < len(texto) and texto[pos].isspace():
        pos += 1
    m = _DO_SIMPLE.match(texto, pos)
    if m:
        fin = _cierre_do(texto, m.end())
        return texto[m.end() : fin], _punto_y_coma(texto, fin) + 1
    fin = _punto_y_coma(texto, pos)
    return texto[pos : fin + 1], fin + 1


def _si(texto: str, i: int, m: re.Match, ambito: dict[str, str], est: _Estado) -> tuple[int, str]:
    condicion = _procesar(m.group(1), ambito, est).strip()
    cierta = _evaluar_condicion(condicion)
    rama_si, pos = _rama(texto, m.end(), ambito, est)
    rama_no = ""
    otra = _ELSE.match(texto, pos)
    if otra:
        rama_no, pos = _rama(texto, otra.end(), ambito, est)
    elegida = rama_si if cierta else rama_no
    return pos, _procesar(elegida, ambito, est)


def _evaluar_condicion(condicion: str) -> bool:
    """Compara textos como %IF de SAS: `=`, `^=`, `~=` o `<>`. Sin operador no se acepta."""
    m = _COMPARACION.match(condicion)
    if not m:
        raise ErrorMacro(f"condición de %if no soportada: {condicion!r}")
    izquierda, operador, derecha = m.group(1).strip(), m.group(2), m.group(3).strip()
    if operador == "=":
        return izquierda == derecha
    return izquierda != derecha


def _bucle(texto: str, m: re.Match, ambito: dict[str, str], est: _Estado) -> tuple[int, str]:
    variable = m.group(1)
    inicio = int(_procesar(m.group(2), ambito, est).strip())
    fin = int(_procesar(m.group(3), ambito, est).strip())
    cuerpo_inicio = m.end()
    cuerpo_fin = _cierre_do(texto, cuerpo_inicio)
    cuerpo = texto[cuerpo_inicio:cuerpo_fin]
    salida: list[str] = []
    for valor in range(inicio, fin + 1):
        local = dict(ambito, **{variable: str(valor)})
        salida.append(_procesar(cuerpo, local, est))
        ambito[variable] = str(valor)
    return _punto_y_coma(texto, cuerpo_fin) + 1, "".join(salida)


def _funcion_macro(nombre: str, interior: str, ambito: dict[str, str], est: _Estado) -> str:
    if nombre == "str":
        return interior
    resuelto = _procesar(interior, ambito, est).strip()
    if nombre == "eval":
        if not _ENTERO_EXPR.match(resuelto):
            raise ErrorMacro(f"%eval solo admite enteros y + - *: {resuelto!r}")
        return str(_entero_seguro(ast.parse(resuelto, mode="eval").body))
    m = _CALL_FUNC.match(resuelto)
    if not m or m.group(1) not in FUNCIONES:
        raise ErrorMacro(f"%sysfunc no soportado en la capa B: {resuelto!r}")
    argumentos = [_argumento(a.strip()) for a in m.group(2).split(",")] if m.group(2) else []
    return str(evaluar(m.group(1), *argumentos))


def _llamar(texto: str, m: re.Match, ambito: dict[str, str], est: _Estado) -> tuple[int, str]:
    parametros, cuerpo = est.macros[m.group(1)]
    pos = m.end()
    valores: list[str] = []
    if pos < len(texto) and texto[pos] == "(":
        interior, pos = _parentesis(texto, pos)
        valores = [_procesar(a, ambito, est).strip() for a in _partir(interior)]
    if len(valores) != len(parametros):
        raise ErrorMacro(
            f"%{m.group(1)} espera {len(parametros)} argumentos, llegaron {len(valores)}"
        )
    local = dict(ambito, **dict(zip(parametros, valores, strict=True)))
    if pos < len(texto) and texto[pos] == ";":
        pos += 1
    return pos, _procesar(cuerpo, local, est)
