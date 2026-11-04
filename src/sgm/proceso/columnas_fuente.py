"""Columnas que el programa SAS demuestra para los datasets importados desde archivos externos.

Un `PROC IMPORT` de Excel no trae su esquema en el SAS. Lo único que el programa demuestra son las
columnas que usa de ese dataset: en `PROC SQL` con alias (`t.COL`, `t.'COL'n`), en
`SELECT col INTO :var FROM ...` y en el `rename=` de un `SET` o `DATA`. Este módulo saca solo esas
columnas y no supone ninguna más. Un dataset sin columnas usadas queda con lista vacía, y eso es un
esquema pendiente.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ImportacionExcel:
    """Un `PROC IMPORT` con ruta de origen y dataset de salida (`WORK.`, sin el prefijo)."""

    ruta: str
    dataset: str
    linea: int


# Cadenas (se saltan), comentarios `/* ... */`, `*` (que solo es comentario al inicio de una
# sentencia) y el `;` que separa sentencias.
_TOKENS = re.compile(r"'[^']*'|\"[^\"]*\"|/\*.*?\*/|\*|;", re.DOTALL)
_COMENTARIO_BLOQUE = re.compile(r"/\*.*?\*/", re.DOTALL)

_PROC_IMPORT = re.compile(r"\bPROC\s+IMPORT\b(.*?)\bRUN\s*;", re.IGNORECASE | re.DOTALL)
_DATAFILE = re.compile(r"\b(?:DATAFILE|FILE)\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
_OUT = re.compile(r"\bOUT\s*=\s*(?:WORK\.)?(\w+)(?![\w.])", re.IGNORECASE)

# Palabras que pueden seguir a FROM/JOIN sin ser alias de la tabla.
_RESERVADAS = frozenset(
    {
        "AND",
        "AS",
        "CROSS",
        "FROM",
        "FULL",
        "GROUP",
        "HAVING",
        "INNER",
        "INTO",
        "JOIN",
        "LEFT",
        "LIMIT",
        "ON",
        "OR",
        "ORDER",
        "OUTER",
        "RIGHT",
        "SELECT",
        "SET",
        "UNION",
        "USING",
        "WHERE",
        "WHEN",
    }
)

_FROM_JOIN = r"(?<![\w.])(?:FROM|JOIN)\s+(?:WORK\.)?{nombre}(?![\w.])(?:\s+(?:AS\s+)?(\w+))?"
_INTO = re.compile(
    r"\bSELECT\s+(?:DISTINCT\s+)?(?:(\w+)\.)?(?:'([^']+)'n|(\w+))\s+INTO\s*:", re.IGNORECASE
)
_RENAME = re.compile(r"\brename\s*=\s*(\([^)]*\)|\w+\s*=\s*\w+)", re.IGNORECASE)
_PAR_VIEJO_NUEVO = re.compile(r"(\w+)\s*=\s*\w+")


def _sentencias(texto: str) -> tuple[str, list[tuple[int, str]]]:
    """Quita los comentarios y parte el texto en sentencias.

    Devuelve el texto limpio (misma longitud que el original) y una lista de pares
    `(desplazamiento, texto de la sentencia)`. Los `;` dentro de cadenas no cortan.
    """
    partes: list[str] = []
    ultimo = 0  # hasta dónde ya se copió el texto original
    cortes: list[int] = []
    desde = 0  # inicio de la sentencia en curso
    pos = 0
    while (m := _TOKENS.search(texto, pos)) is not None:
        inicio, fin = m.span()
        token = m.group()
        pos = fin
        if token[0] in "'\"":
            continue
        if token == ";":
            cortes.append(inicio)
            desde = fin
            continue
        if token == "*":
            if not _solo_comentarios(texto[desde:inicio]):
                continue
            # Comentario de sentencia: se borra hasta su `;` inclusive.
            fin_comentario = texto.find(";", inicio)
            fin = len(texto) if fin_comentario < 0 else fin_comentario + 1
            pos = desde = fin
        partes.append(texto[ultimo:inicio])
        partes.append(re.sub(r"[^\n]", " ", texto[inicio:fin]))
        ultimo = fin
    partes.append(texto[ultimo:])
    limpio = "".join(partes)

    segmentos: list[tuple[int, str]] = []
    inicio = 0
    for corte in [*cortes, len(limpio)]:
        trozo = limpio[inicio:corte]
        if trozo.strip():
            segmentos.append((inicio, trozo))
        inicio = corte + 1
    return limpio, segmentos


def _solo_comentarios(texto: str) -> bool:
    """Cierto si el texto solo tiene espacios y comentarios de bloque."""
    return not _COMENTARIO_BLOQUE.sub("", texto).strip()


def datasets_importados(texto: str) -> list[ImportacionExcel]:
    """Lista cada `PROC IMPORT` que tiene `DATAFILE=` (o `FILE=`) y `OUT=`.

    Solo cuenta los `OUT=` de la biblioteca `WORK`. Las importaciones sin alguno de los dos
    valores se ignoran. La línea es la del `PROC`, contando desde 1.
    """
    limpio, _ = _sentencias(texto)
    return _importaciones(limpio)


def _importaciones(limpio: str) -> list[ImportacionExcel]:
    resultado: list[ImportacionExcel] = []
    for m in _PROC_IMPORT.finditer(limpio):
        bloque = m.group(1)
        ruta = _DATAFILE.search(bloque)
        salida = _OUT.search(bloque)
        if ruta is None or salida is None:
            continue
        linea = limpio.count("\n", 0, m.start()) + 1
        resultado.append(ImportacionExcel(ruta.group(2), salida.group(1), linea))
    return resultado


def columnas_usadas(texto: str, dataset: str) -> list[str]:
    """Columnas de `dataset` que el programa referencia, sin repetir y en orden de aparición."""
    _, segmentos = _sentencias(texto)
    return _columnas_en_segmentos(segmentos, dataset)


def columnas_por_importacion(texto: str) -> dict[str, list[str]]:
    """Mapa `ruta -> columnas usadas de su dataset`. Lista vacía significa esquema pendiente."""
    limpio, segmentos = _sentencias(texto)
    resultado: dict[str, list[str]] = {}
    for imp in _importaciones(limpio):
        previas = resultado.get(imp.ruta, [])
        hallados = _columnas_en_segmentos(segmentos, imp.dataset)
        resultado[imp.ruta] = _unicas([*previas, *hallados])
    return resultado


def _columnas_en_segmentos(segmentos: list[tuple[int, str]], dataset: str) -> list[str]:
    encontradas: list[tuple[int, str]] = []
    for base, sentencia in segmentos:
        for pos, columna in _columnas_de_sentencia(sentencia, dataset):
            encontradas.append((base + pos, columna))
    encontradas.sort(key=lambda par: par[0])
    return _unicas(columna for _, columna in encontradas)


def _unicas(nombres: Iterable[str]) -> list[str]:
    """Quita repetidos sin distinguir mayúsculas y conserva la primera aparición."""
    vistos: set[str] = set()
    salida: list[str] = []
    for nombre in nombres:
        clave = nombre.casefold()
        if clave not in vistos:
            vistos.add(clave)
            salida.append(nombre)
    return salida


def _columnas_de_sentencia(sentencia: str, dataset: str) -> list[tuple[int, str]]:
    """Columnas de `dataset` en una sentencia, con su posición dentro de la sentencia."""
    hallados = _rename(sentencia, dataset)
    aliases = _aliases(sentencia, dataset)
    if aliases:
        hallados += _por_alias(sentencia, aliases)
        hallados += _por_into(sentencia, aliases)
    return hallados


def _aliases(sentencia: str, dataset: str) -> list[str]:
    """Alias con los que la sentencia nombra `dataset` en FROM o JOIN.

    Sin alias explícito, el alias es el propio nombre del dataset.
    """
    patron = re.compile(_FROM_JOIN.format(nombre=re.escape(dataset)), re.IGNORECASE)
    salida: list[str] = []
    for m in patron.finditer(sentencia):
        alias = m.group(1)
        if alias is None or alias.upper() in _RESERVADAS:
            alias = dataset
        salida.append(alias)
    return _unicas(salida)


def _por_alias(sentencia: str, aliases: list[str]) -> list[tuple[int, str]]:
    """Regla 1: `alias.columna` o `alias.'columna'n` en la misma sentencia."""
    hallados: list[tuple[int, str]] = []
    for alias in aliases:
        patron = re.compile(
            r"(?<![\w.])" + re.escape(alias) + r"\.(?:'([^']+)'n|(\w+))", re.IGNORECASE
        )
        for m in patron.finditer(sentencia):
            grupo = 1 if m.group(1) is not None else 2
            hallados.append((m.start(grupo), m.group(grupo)))
    return hallados


def _por_into(sentencia: str, aliases: list[str]) -> list[tuple[int, str]]:
    """Regla 2: `SELECT columna INTO :variable` cuando la sentencia lee el dataset."""
    permitidos = {alias.casefold() for alias in aliases}
    hallados: list[tuple[int, str]] = []
    for m in _INTO.finditer(sentencia):
        calificador = m.group(1)
        if calificador is not None and calificador.casefold() not in permitidos:
            continue
        if m.group(2) is not None:
            hallados.append((m.start(2), m.group(2)))
        else:
            hallados.append((m.start(3), m.group(3)))
    return hallados


def _rename(sentencia: str, dataset: str) -> list[tuple[int, str]]:
    """Regla 3: `[WORK.]dataset(rename=Viejo=Nuevo)` o `rename=(a=b c=d)`.

    Aporta el nombre viejo de cada par, que es la columna que el dataset trae.
    """
    patron = re.compile(
        r"(?<![\w.])(?:WORK\.)?" + re.escape(dataset) + r"(?![\w.])\s*\(", re.IGNORECASE
    )
    hallados: list[tuple[int, str]] = []
    for m in patron.finditer(sentencia):
        inicio, opciones = _contenido_parentesis(sentencia, m.end() - 1)
        for r in _RENAME.finditer(opciones):
            grupo = r.group(1)
            for par in _PAR_VIEJO_NUEVO.finditer(grupo):
                pos = inicio + r.start(1) + par.start(1)
                hallados.append((pos, par.group(1)))
    return hallados


def _contenido_parentesis(sentencia: str, abre: int) -> tuple[int, str]:
    """Texto entre el paréntesis de `abre` y su cierre. Devuelve también su desplazamiento."""
    profundidad = 0
    for i in range(abre, len(sentencia)):
        if sentencia[i] == "(":
            profundidad += 1
        elif sentencia[i] == ")":
            profundidad -= 1
            if profundidad == 0:
                return abre + 1, sentencia[abre + 1 : i]
    return abre + 1, sentencia[abre + 1 :]
