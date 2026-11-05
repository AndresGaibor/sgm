"""R1-12: la regla de duplicados que el SAS demuestra, leída del programa.

Un `PROC SORT` con `NODUPKEY` conserva **una fila por llave**. La regla que el caso fija es la
primera fila de cada llave en el orden de entrada, porque la opción `EQUALS` (la que SAS aplica
por defecto) mantiene el orden original de las filas dentro de cada grupo `BY`. El caso
`L8/totales/01_duplicados_frecuencias` lo declara en sus `supuestos`, y la documentación de SAS
que cita dice lo mismo; el Job lo confirma ejecutando (ver `tools/prueba_duplicados.py`).

Lo que no se lee como regla y sale como `Pendiente:`:

* `NOEQUALS`: SAS no garantiza qué fila conserva dentro de la llave.
* `NODUPREC` (`BY _ALL_`): duplicados exactos. No se traduce en esta rama.
* `DESCENDING` en el `BY`: no cambia qué fila se conserva, pero no se ha demostrado.

Traducción a Talend (ver `talend_item/flujos_duplicados.py`): `tMap` que recorta los blancos
finales de las llaves, y `tUniqRow` con `CASE_SENSITIVE` sobre esas llaves. `tUniqRow` saca la
primera fila que llega por cada llave; con un flujo sin ordenar, esa es la primera en el orden de
entrada. No se usa `tSortRow`: el orden de salida no es parte de la regla (el SAS deja las filas
ordenadas por la llave, pero la comparación del caso es por multiconjunto).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Una sentencia `PROC SORT` seguida de su `BY`, sin comentarios `/* */`.
_COMENTARIO = re.compile(r"/\*.*?\*/", re.DOTALL)
_PASO = re.compile(r"(?is)\bPROC\s+SORT\b(?P<opciones>[^;]*);(?P<by>\s*BY\b[^;]*;)?")
_DATA = re.compile(r"(?i)\bDATA\s*=\s*(?:WORK\.)?(?P<tabla>\w+)")
_OUT = re.compile(r"(?i)\bOUT\s*=\s*(?:WORK\.)?(?P<tabla>\w+)")
_TOKEN_NODUPKEY = re.compile(r"(?i)\bNODUPKEY\b")
_TOKEN_NODUPREC = re.compile(r"(?i)\bNODUP(?:REC)?\b")
_EQUALS = re.compile(r"(?i)\bNOEQUALS\b")
_DESCENDING = re.compile(r"(?i)\bDESCENDING\b")

MOTIVO = (
    "PROC SORT NODUPKEY EQUALS: se conserva la primera fila de cada llave en el orden de entrada"
)


@dataclass(frozen=True)
class ReglaDuplicados:
    """Una sentencia `NODUPKEY` demostrada: qué tabla entra, cuál sale y por qué llaves."""

    entrada: str  # DATA=, sin WORK.
    salida: str  # OUT=, sin WORK.
    llaves: tuple[str, ...]  # BY, en orden
    equals: bool  # EQUALS: la primera fila de cada llave en el orden de entrada
    motivo: str = MOTIVO


def _pendiente(paso: str, motivo: str) -> str:
    return f"R1-12: PROC SORT {paso}: {motivo}"


def _llaves(by: str) -> tuple[str, ...]:
    texto = re.sub(r"(?i)^\s*BY\b", "", by).replace(";", "").strip()
    llaves = tuple(texto.split())
    if not llaves:
        raise ValueError("PROC SORT NODUPKEY sin BY: no hay llave con la que quitar repetidos")
    return llaves


def leer_reglas(texto: str) -> tuple[list[ReglaDuplicados], list[str]]:
    """Reglas `NODUPKEY` que el programa demuestra, y los pasos de duplicados que no se traducen.

    Devuelve `(reglas, pendientes)`. Lanza `ValueError` si una sentencia `NODUPKEY` no tiene su
    `DATA=`, su `OUT=` o su `BY`: sin ellos no hay nada que emitir.
    """
    limpio = _COMENTARIO.sub(" ", texto)
    reglas: list[ReglaDuplicados] = []
    pendientes: list[str] = []
    for paso in _PASO.finditer(limpio):
        opciones, by = paso.group("opciones"), paso.group("by") or ""
        if _TOKEN_NODUPKEY.search(opciones):
            entrada = _DATA.search(opciones)
            salida = _OUT.search(opciones)
            if entrada is None or salida is None:
                raise ValueError(f"PROC SORT NODUPKEY sin DATA= u OUT=: {opciones.strip()}")
            llaves = _llaves(by)
            if _DESCENDING.search(by):
                pendientes.append(_pendiente(salida["tabla"], "BY con DESCENDING, no demostrado"))
                continue
            if _EQUALS.search(opciones):
                pendientes.append(
                    _pendiente(salida["tabla"], "NOEQUALS no fija qué fila se conserva")
                )
                continue
            reglas.append(
                ReglaDuplicados(entrada["tabla"], salida["tabla"], llaves, equals=True)
            )
        elif _TOKEN_NODUPREC.search(opciones):
            destino = _OUT.search(opciones)
            tabla = destino["tabla"] if destino else "sin OUT="
            pendientes.append(_pendiente(tabla, "NODUPREC (duplicados exactos) no se traduce aquí"))
    return reglas, pendientes


def regla_de_salida(texto: str, salida: str) -> ReglaDuplicados:
    """La regla `NODUPKEY` que produce `salida`; `ValueError` si no hay ninguna."""
    reglas, _ = leer_reglas(texto)
    coincidentes = [r for r in reglas if r.salida.upper() == salida.upper()]
    if len(coincidentes) != 1:
        raise ValueError(
            f"Se esperaba una regla NODUPKEY para {salida}; hay {len(coincidentes)} en el SAS"
        )
    return coincidentes[0]


__all__ = ["MOTIVO", "ReglaDuplicados", "leer_reglas", "regla_de_salida"]
