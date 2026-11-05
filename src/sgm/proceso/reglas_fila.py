"""Filtros de fila de `NRO_DOC` vacío o cero, leídos del `WHERE` del SAS (R1-04 / T13).

El programa escribe la misma terna de consultas por producto:

- `WHERE ( ( col = 0 ) OR col IS MISSING ) AND ( rel <> 9902 )` -> titulares y cotitulares;
- la misma con `rel = 9902` -> firmas autorizadas (FA);
- `WHERE col IS NOT MISSING AND ( col <> 0 )` -> documentos no vacíos ni cero.

Columnas, valores y tablas de destino salen del SAS: no se declaran en YAML. Solo se reconocen
sentencias `CREATE TABLE ... AS SELECT` con `WHERE`. La regla "Campos vacios" (una larga cadena de
`IS MISSING` sobre 19 columnas) no tiene la forma `= 0 OR ... IS MISSING` y **no** entra aquí:
queda para la parte 2 de R1-04, con su propio caso del corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.columnas_fuente import _sentencias as _partir

_CREATE = re.compile(
    r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<destino>[\w$&]+)\s+AS\s+(?P<cuerpo>SELECT\b.*)$"
)
_WHERE = re.compile(r"(?i)\bWHERE\b")
# En el programa real el alias es `SABANA_NO_DUPLICADOS_AHO.NRO_DOC`; en el corpus v02 es
# `SABANA_&sufijo..NRO_DOC` (el punto extra es el separador de la macro). `\.+` cubre los dos.
_REF = r"(?P<cal>[\w$&]+)\.+(?P<col>[\w$]+)"
_REF2 = r"(?P=cal)\.+(?P=col)"
# `( ALIAS.NRO_DOC = 0 ) OR ALIAS.NRO_DOC IS MISSING`, con o sin paréntesis alrededor del `=`.
_VACIO_CERO = re.compile(
    rf"(?is){_REF}\s*=\s*0\s*\)\s*OR\s+{_REF2}\s+IS\s+MISSING"
)
_VALIDO = re.compile(
    rf"(?is){_REF}\s+IS\s+NOT\s+MISSING\s+AND\s*\(\s*{_REF2}\s*<>\s*0\s*\)"
)
_RELACION = re.compile(
    r"(?is)(?P<cal>[\w$&]+)\.+(?P<col>[\w$]+)\s*(?P<op><>|!=|=)\s*(?P<valor>\d+)\s*\)"
)
MODOS = ("tit_cot", "fa", "valido")


@dataclass(frozen=True)
class ReglaFila:
    """Un `WHERE` que separa un flujo de filas, con la línea del SAS que lo demuestra."""

    destino: str  # tabla que crea la consulta, sin `WORK.`
    columna: str  # NRO_DOC
    modo: str  # tit_cot | fa | valido
    linea: int
    columna_relacion: str = ""  # RELACION; vacío en `valido`
    valor_relacion: str = ""  # 9902; vacío en `valido`
    operador_relacion: str = ""  # <> en tit_cot, = en fa; vacío en `valido`

    @property
    def vacio_o_cero(self) -> bool:
        return self.modo != "valido"


def _relacion(filtro: str, columna: str) -> re.Match[str] | None:
    """El `rel = 9902` / `rel <> 9902` del `WHERE`, descartando el `col = 0` de la propia regla."""
    for m in _RELACION.finditer(filtro):
        if m.group("valor") != "0" and m.group("col").casefold() != columna.casefold():
            return m
    return None


def reglas_fila(texto: str) -> list[ReglaFila]:
    """Reglas de vacío/cero en el orden en que aparecen en el programa."""
    resultado: list[ReglaFila] = []
    for desplazamiento, sentencia in _partir(texto)[1]:
        crear = _CREATE.search(sentencia)
        if crear is None:
            continue
        donde = _WHERE.search(crear.group("cuerpo"))
        if donde is None:
            continue
        filtro = crear.group("cuerpo")[donde.end() :]
        linea = texto.count("\n", 0, desplazamiento) + 1
        destino = crear.group("destino")
        valido = _VALIDO.search(filtro)
        if valido is not None:
            resultado.append(
                ReglaFila(destino, valido.group("col"), "valido", linea)
            )
            continue
        vacio = _VACIO_CERO.search(filtro)
        if vacio is None:
            continue
        relacion = _relacion(filtro, vacio.group("col"))
        if relacion is None:
            continue
        operador = relacion.group("op")
        modo = "tit_cot" if operador in ("<>", "!=") else "fa"
        resultado.append(
            ReglaFila(
                destino,
                vacio.group("col"),
                modo,
                linea,
                relacion.group("col"),
                relacion.group("valor"),
                operador,
            )
        )
    return resultado


def por_modo(reglas: list[ReglaFila], modo: str) -> list[ReglaFila]:
    """Reglas de un modo; falla si el modo no es uno de los tres conocidos."""
    if modo not in MODOS:
        raise ValueError(f"Modo desconocido: {modo!r}")
    return [r for r in reglas if r.modo == modo]


__all__ = ["MODOS", "ReglaFila", "por_modo", "reglas_fila"]
