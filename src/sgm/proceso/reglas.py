"""Reglas de rango con las que el SAS rechaza filas por un valor fuera de lo permitido.

El programa no usa listas `IN (...)`: usa `NOT BETWEEN <desde> AND <hasta>` sobre una columna y,
ademas, una columna de control igual a un valor fijo. El motivo no se supone: sale del paso `DATA`
que etiqueta la tabla de rechazos (`INCONSISTENCIA='...'`).

Los valores salen del SAS tal como estan escritos; si el programa no declara el motivo, la regla se
devuelve con motivo vacio y queda pendiente.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.columnas_fuente import _sentencias as _partir

_CREATE = re.compile(
    r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<destino>\w+)\s+AS\s+(?P<cuerpo>SELECT\b.*)$"
)
_RANGO = re.compile(
    r"(?is)\b(?P<cal>[\w$]+)\.(?P<col>[\w$]+)\s+(?P<neg>NOT\s+)?BETWEEN\s+"
    r"(?P<desde>-?\d+)\s+AND\s+(?P<hasta>-?\d+)"
)
_FIJO = re.compile(
    r"(?is)\b(?P<cal>[\w$]+)\.(?P<col>[\w$]+)\s*=\s*(?P<valor>'[^']*'|-?\d+(?:\.\d+)?)"
)
_SET = re.compile(r"(?is)\bset\s+(?:WORK\.)?(?P<tabla>\w+)\s*;")
_MOTIVO = re.compile(r"(?is)\bINCONSISTENCIA\s*=\s*'(?P<motivo>[^']*)'")
_WHERE = re.compile(r"(?i)\bWHERE\b")
_FIN = re.compile(r"(?i)\b(?:GROUP\s+BY|ORDER\s+BY|HAVING)\b")


@dataclass(frozen=True)
class ReglaRango:
    """Una columna permitida solo dentro de un rango, para las filas que cumplen el control."""

    destino: str
    columna: str
    desde: int
    hasta: int
    permite: bool
    motivo: str
    linea: int
    control: tuple[str, str] | None = None

    @property
    def condicion(self) -> str:
        """Condicion de Java equivalente, con las columnas recibidas por `fila`."""
        if self.permite:
            rango = f"fila.{self.columna} >= {self.desde} && fila.{self.columna} <= {self.hasta}"
        else:
            rango = f"(fila.{self.columna} < {self.desde} || fila.{self.columna} > {self.hasta})"
        if self.control is None:
            return rango
        columna, valor = self.control
        return f"{rango} && fila.{columna} == {valor}"


def reglas(texto: str) -> list[ReglaRango]:
    """Reglas de rango del programa, con el motivo que el propio SAS les pone."""
    resultado: list[ReglaRango] = []
    posiciones = _sentencias(texto)
    for desplazamiento, sentencia in posiciones:
        crear = _CREATE.search(sentencia)
        if crear is None:
            continue
        where = _WHERE.search(crear.group("cuerpo"))
        if where is None:
            continue
        cola = crear.group("cuerpo")[where.end() :]
        fin = _FIN.search(cola)
        if fin:
            cola = cola[: fin.start()]
        rango = _RANGO.search(cola)
        if rango is None:
            continue
        linea = texto.count("\n", 0, desplazamiento) + sentencia.count(
            "\n", 0, crear.start("cuerpo") + where.end() + rango.start()
        ) + 1
        control = _control(cola)
        destino = crear.group("destino")
        resultado.append(
            ReglaRango(
                destino=destino,
                columna=rango.group("col"),
                desde=int(rango.group("desde")),
                hasta=int(rango.group("hasta")),
                permite=rango.group("neg") is None,
                motivo=_motivo(texto, desplazamiento, destino),
                linea=linea,
                control=control,
            )
        )
    return resultado


def _sentencias(texto: str) -> list[tuple[int, str]]:
    """Sentencias del programa sin comentarios, con su desplazamiento en el texto original."""
    return _partir(texto)[1]


def _control(cola: str) -> tuple[str, str] | None:
    """Columna de control y valor fijo del `WHERE`, si la regla lo exige."""
    for m in _FIJO.finditer(cola):
        return m.group("col"), m.group("valor")
    return None


def _motivo(texto: str, desde: int, destino: str) -> str:
    """Motivo que el SAS escribe en la tabla de rechazos `destino`."""
    ventana = texto[desde : desde + 6000]
    for m in _SET.finditer(ventana):
        if m.group("tabla").casefold() == destino.casefold():
            motivo = _MOTIVO.search(ventana, m.end())
            if motivo is not None:
                return motivo.group("motivo")
    return ""
