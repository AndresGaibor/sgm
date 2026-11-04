"""Tablas que lee una sentencia SQL de PROC SQL (FROM, listas con coma, JOIN y subconsultas).

El SQL se tokeniza ignorando comentarios y literales, y luego se agrupa por paréntesis.
Un `from` dentro de una llamada a función (`extract(año from x)`, `substring(a from 2)`,
`trim(both x from y)`) no abre fuente; las subconsultas que hay dentro sí se recorren.
Los alias de tabla y de subconsulta no son fuentes; los nombres de CTE tampoco.
Lo que no se puede resolver (p. ej. `&tabla.`) se devuelve tal cual aparece.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TOKEN = re.compile(
    r"""
    (?P<comentario>/\*.*?\*/|--[^\n]*)
    |(?P<nombre>"(?:[^"]|"")*"|'(?:[^']|'')*'[nN](?!\w))
    |(?P<literal>'(?:[^']|'')*')
    |(?P<palabra>[\w.&]+)
    |(?P<signo>[(),;])
    """,
    re.DOTALL | re.VERBOSE,
)

# Palabras que, seguidas de `(`, no forman una llamada a función.
_NO_FUNCION = frozenset(
    {
        "in", "exists", "any", "all", "some", "and", "or", "not", "on", "where", "having",
        "from", "join", "select", "with", "values", "as", "by", "when", "then", "else",
        "case", "between", "union", "except", "intersect", "using", "set", "into", "is",
        "like", "distinct", "over", "if", "limit",
    }
)  # fmt: skip

# Cláusulas que terminan la lista de FROM.
_CORTE = frozenset(
    {
        "where", "group", "having", "order", "union", "except", "intersect", "into",
        "limit", "set", "quit", "select",
    }
)  # fmt: skip

# Palabras que no pueden ser alias de una tabla.
_NO_ALIAS = _CORTE | frozenset(
    {
        "join", "inner", "left", "right", "full", "cross", "natural", "outer", "on",
        "using", "from", "and", "or", "not", "lateral", "end", "when", "then", "else",
    }
)  # fmt: skip


@dataclass(eq=False)
class _Grupo:
    """Contenido entre un `(` y su `)`. `funcion` indica una llamada a función."""

    funcion: bool
    hijos: list = field(default_factory=list)  # tokens (tuplas) o _Grupo


@dataclass
class _Acumulador:
    ctes: frozenset[str]
    tablas: list[str] = field(default_factory=list)

    def agregar(self, nombre: str) -> None:
        if nombre.lower() in self.ctes or nombre in self.tablas:
            return
        self.tablas.append(nombre)


def _tokenizar(sql: str) -> list[tuple[str, str]]:
    """Devuelve (tipo, texto) sin comentarios. El texto es el original, sin tocar mayúsculas."""
    return [(m.lastgroup, m.group()) for m in _TOKEN.finditer(sql) if m.lastgroup != "comentario"]


def _construir(tokens: list[tuple[str, str]]) -> _Grupo:
    raiz = _Grupo(funcion=False)
    pila = [raiz]
    for tipo, texto in tokens:
        actual = pila[-1]
        if tipo == "signo" and texto == "(":
            previo = actual.hijos[-1] if actual.hijos else None
            es_funcion = (
                isinstance(previo, tuple)
                and previo[0] == "palabra"
                and previo[1].lower() not in _NO_FUNCION
            )
            grupo = _Grupo(funcion=es_funcion)
            actual.hijos.append(grupo)
            pila.append(grupo)
        elif tipo == "signo" and texto == ")":
            if len(pila) > 1:
                pila.pop()
        else:
            actual.hijos.append((tipo, texto))
    return raiz


def _es_palabra(nodo, *palabras: str) -> bool:
    return isinstance(nodo, tuple) and nodo[0] == "palabra" and nodo[1].lower() in palabras


def _es_nombre(nodo) -> bool:
    return isinstance(nodo, tuple) and nodo[0] in ("palabra", "nombre")


def _saltar_alias(hijos: list, i: int) -> int:
    """Devuelve el índice que sigue al alias opcional (`[as] alias`) de una fuente."""
    con_as = i < len(hijos) and _es_palabra(hijos[i], "as")
    if con_as:
        i += 1
    if i < len(hijos) and _es_nombre(hijos[i]):
        if con_as or hijos[i][1].lower() not in _NO_ALIAS:
            i += 1
    return i


def _saltar_passthrough(hijos: list, i: int) -> int:
    """Salta `to <motor> (...)` tras `from connection`: no es una tabla de SAS."""
    while i < len(hijos) and not isinstance(hijos[i], _Grupo):
        if _es_palabra(hijos[i], "select", "from", "where", "join"):
            break
        i += 1
    if i < len(hijos) and isinstance(hijos[i], _Grupo):
        i += 1
    return i


def _recorrer(grupo: _Grupo, acc: _Acumulador, esperar: bool = False, en_funcion: bool = False):
    """Recorre los hijos de un grupo en orden de aparición y acumula las fuentes.

    `esperar`: el primer elemento del grupo es una referencia de tabla (p. ej. `from (...)`).
    `en_funcion`: el grupo es una llamada a función; solo importan sus subconsultas.
    """
    hijos = grupo.hijos
    if en_funcion:
        for h in hijos:
            if isinstance(h, _Grupo):
                _recorrer(h, acc, en_funcion=h.funcion)
        return

    en_from = esperar
    espera = esperar
    i = 0
    while i < len(hijos):
        h = hijos[i]
        if isinstance(h, _Grupo):
            if espera and h.funcion:
                # Función de tabla (`from f(x)`): no es una fuente de SAS.
                espera = False
                i += 1
                continue
            if espera:
                _recorrer(h, acc, esperar=True)
                espera = False
                en_from = True
                i = _saltar_alias(hijos, i + 1)
                continue
            _recorrer(h, acc, en_funcion=h.funcion)
            i += 1
            continue

        tipo, texto = h
        bajo = texto.lower()
        if espera:
            espera = False
            if tipo == "palabra" and bajo in ("select", "with"):
                # `from (select ...)`: el contenido es una consulta, sus `from` abren fuentes.
                espera = False
            elif tipo == "palabra" and bajo == "connection":
                i = _saltar_passthrough(hijos, i + 1)
                continue
            elif tipo in ("palabra", "nombre"):
                acc.agregar(texto)
                en_from = True
                i = _saltar_alias(hijos, i + 1)
                continue
            i += 1
            continue

        if tipo == "palabra" and bajo in ("from", "join"):
            espera = True
            en_from = True
        elif tipo == "palabra" and bajo in _CORTE:
            en_from = False
        elif tipo == "signo" and texto == "," and en_from:
            espera = True
        elif tipo == "signo" and texto == ";":
            en_from = False
        i += 1


def _ctes(grupo: _Grupo, hallados: set[str]) -> None:
    """Nombres de CTE: `nombre [(columnas)] as (consulta)`."""
    hijos = grupo.hijos
    for i, h in enumerate(hijos):
        if isinstance(h, _Grupo):
            _ctes(h, hallados)
            continue
        if not _es_nombre(h) or _es_palabra(h, *_NO_FUNCION):
            continue
        j = i + 1
        if j < len(hijos) and isinstance(hijos[j], _Grupo) and hijos[j].funcion:
            j += 1
        if j + 1 < len(hijos) and _es_palabra(hijos[j], "as") and isinstance(hijos[j + 1], _Grupo):
            hallados.add(h[1].lower())


def extract_sources(sql: str) -> tuple[str, ...]:
    """Tablas que lee la consulta, en orden de aparición y sin duplicados.

    Los nombres se devuelven tal como aparecen en el SQL (con `lib.tabla` si lo traen).
    """
    raiz = _construir(_tokenizar(sql))
    ctes: set[str] = set()
    _ctes(raiz, ctes)
    acc = _Acumulador(ctes=frozenset(ctes))
    _recorrer(raiz, acc)
    return tuple(acc.tablas)
