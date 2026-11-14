"""Normaliza funciones SAS sin confundirlas con agregados de PROC SQL."""

from __future__ import annotations

import re

from sgm.migrar.interprete_funciones import FUNCIONES

_AGREGADOS_SQL = frozenset({"sum", "min", "max", "count", "avg"})
_FUNCIONES_FILA_SQL = frozenset({"sum", "min", "max"})
_NOMBRES_FUNCIONES = sorted(FUNCIONES, key=lambda nombre: (-len(nombre), nombre))
_FUNCIONES_SAS = re.compile(
    r"(?i)\b(" + "|".join(re.escape(nombre) for nombre in _NOMBRES_FUNCIONES) + r")\s*(?=\()"
)


def _rangos_protegidos(expresion: str) -> list[tuple[int, int]]:
    """Encuentra cadenas y comentarios para que sus paréntesis no afecten el análisis."""
    rangos: list[tuple[int, int]] = []
    indice = 0
    while indice < len(expresion):
        if expresion.startswith("/*", indice):
            fin = expresion.find("*/", indice + 2)
            fin = len(expresion) if fin < 0 else fin + 2
            rangos.append((indice, fin))
            indice = fin
            continue
        if expresion.startswith("--", indice):
            salto = re.search(r"\r?\n", expresion[indice + 2 :])
            fin = len(expresion) if salto is None else indice + 2 + salto.start()
            rangos.append((indice, fin))
            indice = fin
            continue
        if expresion[indice] in "'\"":
            comilla = expresion[indice]
            inicio = indice
            indice += 1
            while indice < len(expresion):
                if expresion[indice] == comilla:
                    if expresion[indice + 1 : indice + 2] == comilla:
                        indice += 2
                        continue
                    indice += 1
                    break
                indice += 1
            rangos.append((inicio, indice))
            continue
        indice += 1
    return rangos


def _protegido(indice: int, rangos: list[tuple[int, int]]) -> tuple[int, int] | None:
    return next(((inicio, fin) for inicio, fin in rangos if inicio <= indice < fin), None)


def _es_multiargumento(expresion: str, apertura: int, protegidos: list[tuple[int, int]]) -> bool:
    """Reconoce comas en el nivel exterior sin contar cadenas ni comentarios."""
    profundidad = 0
    comas = 0
    for indice in range(apertura, len(expresion)):
        if _protegido(indice, protegidos):
            continue
        caracter = expresion[indice]
        if caracter == "(":
            profundidad += 1
        elif caracter == ")":
            profundidad -= 1
            if profundidad == 0:
                return comas > 0
        elif caracter == "," and profundidad == 1:
            comas += 1
    return False


def normalizar_funciones_sas(expresion: str) -> str:
    """Marca llamadas SAS por fila y conserva los agregados SQL de un argumento."""
    protegidos = _rangos_protegidos(expresion)
    ediciones: list[tuple[int, int, str]] = []
    for coincidencia in _FUNCIONES_SAS.finditer(expresion):
        if _protegido(coincidencia.start(), protegidos):
            continue
        nombre = coincidencia.group(1).lower()
        if nombre in _AGREGADOS_SQL:
            if nombre not in _FUNCIONES_FILA_SQL:
                continue
            apertura = coincidencia.end()
            while apertura < len(expresion) and expresion[apertura].isspace():
                apertura += 1
            comentario = _protegido(apertura, protegidos)
            while comentario is not None and comentario[0] == apertura:
                apertura = comentario[1]
                while apertura < len(expresion) and expresion[apertura].isspace():
                    apertura += 1
                comentario = _protegido(apertura, protegidos)
            if (
                apertura >= len(expresion)
                or expresion[apertura] != "("
                or not _es_multiargumento(expresion, apertura, protegidos)
            ):
                continue
            sustituto = f"sgm_row_{nombre}"
        else:
            sustituto = f"sgm_{nombre}"
        ediciones.append((coincidencia.start(1), coincidencia.end(1), sustituto))
    for inicio, fin, sustituto in reversed(ediciones):
        expresion = expresion[:inicio] + sustituto + expresion[fin:]
    return expresion
