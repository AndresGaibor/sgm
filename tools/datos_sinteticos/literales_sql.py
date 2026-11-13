"""Lee literales SQL simples y reconoce dependencias macro sin evaluarlas."""

from __future__ import annotations

import re

_NUMERO = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?")
_MACRO = re.compile(r"&[A-Za-z_]\w*\.?", re.ASCII)
_MACRO_FUNCION = re.compile(r"%[A-Za-z_]\w*", re.ASCII)


def _macro_sin_terminador(macro: str) -> str:
    return macro[:-1] if macro.endswith(".") else macro


def _leer_macro_funcion(texto: str, inicio: int) -> tuple[str, int] | None:
    """Lee una macro-función con paréntesis balanceados sin evaluarla."""
    nombre = _MACRO_FUNCION.match(texto, inicio)
    if nombre is None:
        return None
    fin_nombre = nombre.end()
    pos = fin_nombre
    while pos < len(texto) and texto[pos].isspace():
        pos += 1
    if pos >= len(texto) or texto[pos] != "(":
        return nombre.group(), fin_nombre
    profundidad = 0
    comilla = ""
    for i in range(pos, len(texto)):
        caracter = texto[i]
        if comilla:
            if caracter == comilla:
                comilla = ""
        elif caracter in "'\"":
            comilla = caracter
        elif caracter == "(":
            profundidad += 1
        elif caracter == ")":
            profundidad -= 1
            if profundidad == 0:
                return texto[inicio : i + 1].strip(), i + 1
    return texto[inicio:].strip(), len(texto)


def _macros_en_texto(texto: str) -> list[str]:
    """Lista referencias y llamadas macro visibles en un literal doble."""
    halladas: list[tuple[int, str]] = []
    halladas.extend(
        (match.start(), _macro_sin_terminador(match.group()))
        for match in _MACRO.finditer(texto)
    )
    for match in _MACRO_FUNCION.finditer(texto):
        llamada = _leer_macro_funcion(texto, match.start())
        if llamada:
            halladas.append((match.start(), llamada[0]))
    return [contenido for _, contenido in sorted(halladas)]


def predicado_negado(texto: str, posicion: int) -> bool:
    """Detecta negación directa o un grupo negado antes de una comparación."""
    pila: list[bool] = []
    for posicion_actual, caracter in enumerate(texto[:posicion]):
        if caracter == "(":
            previo = texto[:posicion_actual].rstrip()
            pila.append(bool(re.search(r"\bNOT$", previo, re.IGNORECASE)))
        elif caracter == ")" and pila:
            pila.pop()
    if sum(pila) % 2:
        return True
    return bool(re.search(r"\bNOT$", texto[:posicion].rstrip(), re.IGNORECASE))


def leer_valor(texto: str, inicio: int) -> tuple[str, str, int] | None:
    """Lee un literal simple o informa macros sin evaluarlas."""
    pos = inicio
    while pos < len(texto) and texto[pos].isspace():
        pos += 1
    if pos >= len(texto):
        return None
    if texto[pos] in "'\"":
        comilla = texto[pos]
        partes: list[str] = []
        j = pos + 1
        while j < len(texto):
            if texto[j] == comilla:
                if j + 1 < len(texto) and texto[j + 1] == comilla:
                    partes.append(comilla)
                    j += 2
                    continue
                contenido = "".join(partes)
                macros = _macros_en_texto(contenido) if comilla == '"' else []
                if macros:
                    return "macro", ", ".join(dict.fromkeys(macros)), j + 1
                return "literal", contenido, j + 1
            partes.append(texto[j])
            j += 1
        return None
    macro = _MACRO.match(texto, pos)
    if macro:
        return "macro", _macro_sin_terminador(macro.group()), macro.end()
    llamada = _leer_macro_funcion(texto, pos)
    if llamada:
        return "macro", llamada[0], llamada[1]
    numero = _NUMERO.match(texto, pos)
    if numero and (numero.end() == len(texto) or texto[numero.end()] not in "._A-Za-z"):
        return "literal", numero.group(), numero.end()
    return None


def valor_cierra_predicado(texto: str, fin: int) -> bool:
    """Comprueba que el valor complete el operando derecho, sin expresión adicional."""
    resto = texto[fin:].lstrip()
    return not resto or bool(re.match(r"(?:\)|;|\bAND\b|\bOR\b)", resto, re.IGNORECASE))


def elementos_in(texto: str, inicio: int) -> tuple[list[str], str | None] | None:
    """Lee miembros literales y acumula macros pendientes sin evaluarlas."""
    pos = inicio
    valores: list[str] = []
    macros: list[str] = []
    while True:
        valor = leer_valor(texto, pos)
        if valor is None:
            return None
        tipo, contenido, pos = valor
        if tipo == "macro":
            macros.append(contenido)
        else:
            valores.append(contenido)
        while pos < len(texto) and texto[pos].isspace():
            pos += 1
        if pos >= len(texto):
            return None
        if texto[pos] == ")":
            return valores, ", ".join(dict.fromkeys(macros)) if macros else None
        if texto[pos] != ",":
            return None
        pos += 1
