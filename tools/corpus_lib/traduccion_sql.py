"""Traducción de SQL de PROC SQL (SAS) a SQLite, con las diferencias de dialecto explícitas.

Cada construcción que se traduce tiene su fila en `DIFERENCIAS.md`. Lo que no se puede traducir con
fidelidad se rechaza con `NoSoportado`: nunca se deja pasar en silencio.
"""

from __future__ import annotations

import re

from .sas_texto import segmentos


class NoSoportado(Exception):
    """Construcción de SAS que el oráculo no traduce con fidelidad."""

    def __init__(self, construccion: str) -> None:
        self.construccion = construccion
        super().__init__(f"Construcción SAS no soportada por el oráculo: {construccion}")


# Funciones de SAS que tienen el mismo significado en SQLite.
FUNCIONES = frozenset(
    {"count", "sum", "min", "max", "avg", "abs", "round", "coalesce", "substr", "upper", "lower"}
)
# Funciones de SAS con otro nombre en SQLite. TRIM de SAS quita solo blancos finales: RTRIM.
RENOMBRES_FUNCION = {"upcase": "upper", "lowcase": "lower", "trim": "rtrim"}
# Palabras que llevan paréntesis sin ser funciones (IN (...), EXISTS (...), ON (...)).
PALABRAS_CON_PARENTESIS = frozenset(
    {
        "in", "exists", "and", "or", "not", "on", "using", "between", "like", "values", "as",
        "from", "where", "select", "join", "case", "when", "then", "else", "having", "is", "by",
        "table", "create", "distinct", "over", "union", "order", "group",
    }
)

_FUNCION = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_CADENA_PROTEGIDA = re.compile("\x01(\\d+)\x01")
_SUFIJO_NOMBRE = re.compile("\x01\\d+\x01[nN]\\b")
_SUFIJO_FECHA = re.compile("\x01\\d+\x01[dDtT]\\b")


def a_sqlite(sql_sas: str) -> str:
    """Traduce una sentencia de PROC SQL de SAS a SQLite.

    Lanza `NoSoportado` con el nombre de la construcción si no puede traducirla con fidelidad.
    """
    cadenas: list[str] = []
    partes: list[str] = []
    for tipo, trozo in segmentos(sql_sas):
        if tipo == "comentario":
            partes.append(" ")
        elif tipo == "cadena":
            # Las cadenas se sacan del texto para que las reglas de palabras no las toquen.
            partes.append(f"\x01{len(cadenas)}\x01")
            cadenas.append(trozo)
        else:
            partes.append(trozo)
    texto = _traducir_codigo("".join(partes))
    return _restaurar_cadenas(texto, cadenas).strip()


def _traducir_codigo(texto: str) -> str:
    """Aplica las reglas al texto donde las cadenas ya están protegidas por marcadores."""
    if _SUFIJO_NOMBRE.search(texto):
        raise NoSoportado('nombre SAS entre comillas con sufijo "n"')
    if _SUFIJO_FECHA.search(texto):
        raise NoSoportado("literal de fecha u hora de SAS ('...'d o '...'t)")
    _rechazar_construcciones(texto)
    texto = re.sub(r"(?i)\bWORK\.(?=[A-Za-z_])", "", texto)
    texto = texto.replace("^=", "<>").replace("~=", "<>")
    texto = re.sub(r"(?i)\bIS\s+NOT\s+MISSING\b", "IS NOT NULL", texto)
    texto = re.sub(r"(?i)\bIS\s+MISSING\b", "IS NULL", texto)
    return _renombrar_funciones(texto)


def _rechazar_construcciones(texto: str) -> None:
    if re.search(r"(?i)\bcalculated\b", texto):
        raise NoSoportado("CALCULATED (alias reutilizado en el mismo SELECT)")
    if re.search(r"(?i)\b(format|informat|label)\s*=", texto):
        raise NoSoportado("FORMAT=, INFORMAT= o LABEL= en el SELECT")
    if re.search(r"(?i)\binto\b", texto):
        raise NoSoportado("INTO (asignación a macrovariables)")
    if "**" in texto:
        raise NoSoportado("potencia (**)")
    if "/" in texto:
        raise NoSoportado("división (/): SAS da decimal y SQLite trunca los enteros")
    if "%" in texto:
        raise NoSoportado("% (módulo en SQLite, no en SAS)")
    if "&" in texto:
        raise NoSoportado("macrovariable (&)")


def _renombrar_funciones(texto: str) -> str:
    def reemplazo(m: re.Match[str]) -> str:
        nombre = m.group(1)
        bajo = nombre.lower()
        if bajo in RENOMBRES_FUNCION:
            return RENOMBRES_FUNCION[bajo] + "("
        if bajo in FUNCIONES or bajo in PALABRAS_CON_PARENTESIS:
            return m.group(0)
        raise NoSoportado(f"función {nombre}()")

    return _FUNCION.sub(reemplazo, texto)


def _restaurar_cadenas(texto: str, cadenas: list[str]) -> str:
    def reemplazo(m: re.Match[str]) -> str:
        original = cadenas[int(m.group(1))]
        if original.startswith('"'):
            # En SAS, "..." es texto. SQLite lo toma como identificador: pasa a comillas simples.
            contenido = original[1:-1].replace('""', '"')
            return "'" + contenido.replace("'", "''") + "'"
        return original

    return _CADENA_PROTEGIDA.sub(reemplazo, texto)
