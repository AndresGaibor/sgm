"""Resuelve fuentes y predicados de consultas PROC SQL sin evaluar expresiones."""

from __future__ import annotations

import re

from sgm.frontend.lexer import split_statements
from sgm.frontend.steps import parse_steps
from sgm.frontend.steps_tipos import ProcSql
from tools.datos_sinteticos.literales_sql import (
    elementos_in,
    leer_valor,
    predicado_negado,
    valor_cierra_predicado,
)

_FUENTES = re.compile(
    r"\b(?:FROM|JOIN)\s+([A-Za-z_][\w$&.]*)"
    r"(?:\s+(?:AS\s+)?([A-Za-z_][\w$]*))?",
    re.IGNORECASE,
)
_DESPUES_DE_COMA = re.compile(
    r",\s*([A-Za-z_][\w$&.]*)"
    r"(?:\s+(?:AS\s+)?([A-Za-z_][\w$]*))?",
    re.IGNORECASE,
)
_INICIO_FROM = re.compile(r"\bFROM\b", re.IGNORECASE)
_FIN_FUENTES = re.compile(
    r"\b(?:JOIN|ON|WHERE|GROUP\s+BY|ORDER\s+BY|HAVING|QUALIFY|UNION|FETCH|LIMIT)\b",
    re.IGNORECASE,
)
_IZQUIERDA = re.compile(
    r"(?<![\w.])(?:(?P<calificador>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\.\s*)?"
    r"(?P<columna>[A-Za-z_]\w*)\s*="
)
_EN = re.compile(
    r"(?<![\w.])(?:(?P<calificador>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\.\s*)?"
    r"(?P<columna>[A-Za-z_]\w*)\s+IN\s*\(",
    re.IGNORECASE,
)
_PREDICADO = re.compile(
    r"(?<![\w.])(?:(?P<calificador>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\.\s*)?"
    r"(?P<columna>[A-Za-z_]\w*)\s*(?:<=|>=|<>|~=|=|<|>|"
    r"(?:NOT\s+)?(?:IN|LIKE|CONTAINS|BETWEEN|IS)\b|"
    r"(?:EQ|NE|LT|LE|GT|GE)\b)",
    re.IGNORECASE,
)
_RESERVADAS_ALIAS = frozenset(
    "AND AS CROSS EXCEPT FULL GROUP HAVING INNER JOIN LEFT LIMIT NOT ON OR ORDER RIGHT "
    "SELECT UNION USING WHERE"
    .split()
)
_FIN_CLAUSULA = re.compile(
    r"\b(?:WHERE|ON|GROUP\s+BY|ORDER\s+BY|HAVING|QUALIFY|UNION|FETCH|LIMIT)\b",
    re.IGNORECASE,
)


def ocultar_cadenas(texto: str) -> str:
    """Enmascara literales con posiciones estables para buscar cláusulas SQL."""
    salida = list(texto)
    i = 0
    while i < len(texto):
        if texto[i] not in "'\"":
            i += 1
            continue
        comilla = texto[i]
        j = i + 1
        while j < len(texto):
            if texto[j] == comilla:
                if j + 1 < len(texto) and texto[j + 1] == comilla:
                    j += 2
                    continue
                j += 1
                break
            j += 1
        for pos in range(i, j):
            if texto[pos] not in "\r\n":
                salida[pos] = " "
        i = j
    return "".join(salida)


def sentencias_sql(texto: str) -> list[str]:
    """Devuelve sentencias SQL reconocidas; para pass-through usa la consulta interna."""
    pasos, _ = parse_steps(split_statements(texto))
    resultado: list[str] = []
    for paso in pasos:
        if not isinstance(paso, ProcSql):
            continue
        for sentencia in paso.statements:
            if sentencia.kind == "select_passthrough" and sentencia.inner_sql:
                resultado.append(sentencia.inner_sql)
            elif sentencia.kind == "execute" and sentencia.inner_sql:
                resultado.append(sentencia.inner_sql)
            elif sentencia.kind != "execute":
                resultado.append(sentencia.text)
    return resultado


def _normalizar_tabla(nombre: str) -> str:
    tabla = nombre.rstrip(".").casefold()
    return tabla if "." in tabla else f"work.{tabla}"


def _alias_tablas(sentencia: str) -> dict[str, str]:
    limpio = ocultar_cadenas(sentencia)
    referencias = [(match.group(1), match.group(2)) for match in _FUENTES.finditer(limpio)]
    for inicio in _INICIO_FROM.finditer(limpio):
        fin = _FIN_FUENTES.search(limpio, inicio.end())
        final = fin.start() if fin else len(limpio)
        tramo = limpio[inicio.end() : final]
        profundidad = 0
        i = 0
        while i < len(tramo):
            if tramo[i] == "(":
                profundidad += 1
            elif tramo[i] == ")":
                profundidad = max(0, profundidad - 1)
            elif tramo[i] == "," and profundidad == 0:
                match = _DESPUES_DE_COMA.match(tramo, i)
                if match:
                    referencias.append((match.group(1), match.group(2)))
                    i = match.end()
                    continue
            i += 1

    candidatos: dict[str, set[str]] = {}
    for nombre_tabla, alias in referencias:
        tabla = _normalizar_tabla(nombre_tabla)
        nombres = {tabla, tabla.rsplit(".", 1)[-1]}
        if alias and alias.upper() not in _RESERVADAS_ALIAS:
            nombres.add(alias.lower())
        for nombre in nombres:
            candidatos.setdefault(nombre, set()).add(tabla)
    return {
        nombre: next(iter(tablas))
        for nombre, tablas in candidatos.items()
        if len(tablas) == 1
    }


def tablas_sql(texto: str) -> list[str]:
    """Lista tablas literales leídas por PROC SQL, conservando el primer orden."""
    salida: list[str] = []
    vistas: set[str] = set()
    for sentencia in sentencias_sql(texto):
        for tabla in _alias_tablas(sentencia).values():
            if tabla not in vistas:
                vistas.add(tabla)
                salida.append(tabla)
    return salida


def _tabla_columna(
    calificador: str | None, columna: str, aliases: dict[str, str]
) -> tuple[str, str] | None:
    tablas = set(aliases.values())
    if calificador:
        tabla = aliases.get(calificador.lower())
        if tabla is None:
            return None
    elif len(tablas) == 1:
        tabla = next(iter(tablas))
    else:
        return None
    return tabla, columna.lower()


def _clausulas(texto: str):
    limpio = ocultar_cadenas(texto)
    inicios = list(re.finditer(r"\b(?:WHERE|ON)\b", limpio, re.IGNORECASE))
    for inicio in inicios:
        fin = _FIN_CLAUSULA.search(limpio, inicio.end())
        final = fin.start() if fin else len(texto)
        yield inicio.end(), final


def valores_exigidos(
    texto: str,
) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """Extrae solo igualdades e IN simples; no evalúa macros ni expresiones."""
    exigidos: dict[str, dict[str, list[str]]] = {}
    dinamicos: list[str] = []
    for sentencia in sentencias_sql(texto):
        aliases = _alias_tablas(sentencia)
        if not aliases:
            continue
        for inicio, fin in _clausulas(sentencia):
            original = sentencia[inicio:fin]
            limpio = ocultar_cadenas(original)
            for match in _IZQUIERDA.finditer(limpio):
                destino = _tabla_columna(
                    match.group("calificador"), match.group("columna"), aliases
                )
                valor = leer_valor(original, match.end())
                if destino is None or valor is None:
                    continue
                tipo, contenido, fin_valor = valor
                if not valor_cierra_predicado(original, fin_valor):
                    continue
                tabla, columna = destino
                if tipo == "macro":
                    linea = f"{tabla}.{columna} = {contenido}"
                    if linea not in dinamicos:
                        dinamicos.append(linea)
                elif not predicado_negado(limpio, match.start()):
                    valores = exigidos.setdefault(tabla, {}).setdefault(columna, [])
                    if contenido not in valores:
                        valores.append(contenido)
            for match in _EN.finditer(limpio):
                if match.group("columna").casefold() == "not":
                    continue
                destino = _tabla_columna(
                    match.group("calificador"), match.group("columna"), aliases
                )
                if destino is None:
                    continue
                resultado = elementos_in(original, match.end())
                if resultado is None:
                    continue
                valores, macro = resultado
                tabla, columna = destino
                if macro:
                    if valores and not predicado_negado(limpio, match.start()):
                        existentes = exigidos.setdefault(tabla, {}).setdefault(columna, [])
                        existentes.extend(v for v in valores if v not in existentes)
                    linea = f"{tabla}.{columna} IN {macro}"
                    if linea not in dinamicos:
                        dinamicos.append(linea)
                elif not predicado_negado(limpio, match.start()):
                    existentes = exigidos.setdefault(tabla, {}).setdefault(columna, [])
                    existentes.extend(v for v in valores if v not in existentes)
    return exigidos, dinamicos


def columnas_en_filtros(texto: str) -> dict[str, list[str]]:
    """Enumera columnas resueltas en predicados, tengan o no valor literal."""
    resultado: dict[str, list[str]] = {}
    for sentencia in sentencias_sql(texto):
        aliases = _alias_tablas(sentencia)
        for inicio, fin in _clausulas(sentencia):
            limpio = ocultar_cadenas(sentencia[inicio:fin])
            for match in _PREDICADO.finditer(limpio):
                destino = _tabla_columna(
                    match.group("calificador"), match.group("columna"), aliases
                )
                if destino is None:
                    continue
                tabla, columna = destino
                columnas = resultado.setdefault(tabla, [])
                if columna not in columnas:
                    columnas.append(columna)
    return resultado
