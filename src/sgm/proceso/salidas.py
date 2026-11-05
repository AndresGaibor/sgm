"""Salidas del producto: tablas de resultado, exportaciones y conciliacion, segun el SAS.

El programa arma el resultado en tablas `WORK` (`SABANA_FINAL_<P>`, `RESULTADO_<P>_NAL`,
`RESULTADO_<P>_EXT`, `INCONS_DEP_<P>`, `INCONS_DEP_CORREGIDA_<P>`) y despues lo escribe con
`PROC EXPORT ... outfile="...csv" dbms=dlm delimiter=';' replace`. Este modulo saca las tablas
con el orden de columnas de su `SELECT` (y la tabla con la que se cruzan, que distingue nacional de
extranjero), las exportaciones con su archivo y su delimitador, y la formula de conciliacion.

Una tabla con `SELECT *` no declara columnas: se devuelve sin ellas y queda pendiente, no se supone
el esquema.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sgm.proceso.columnas_fuente import _sentencias as _partir

_CREATE = re.compile(
    r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<tabla>\w+)\s+AS\s+SELECT\b(?P<lista>.*?)\bFROM\b"
)
_JOIN = re.compile(r"(?is)\bINNER\s+JOIN\s+(?:WORK\.)?(?P<fuente>\w+)")
_COLUMNA = re.compile(r"(?i)(?:\w+\.)?(?:'(?P<literal>[^']+)'n|(?P<nombre>\w+))\s*$")
_EXPORT = re.compile(
    r"(?is)\bproc\s+export\s+data\s*=\s*(?:WORK\.)?(?P<dataset>\w+)\s+outfile\s*=\s*"
    r"(?P<comilla>['\"])(?P<archivo>[^'\"]+)(?P=comilla)(?P<resto>[^;]*);"
)
_DELIMITADOR = re.compile(r"(?i)\bdelimiter\s*=\s*'(?P<delim>[^']*)'")
_REPLACE = re.compile(r"(?i)\breplace\b")
_CONCILIACION = re.compile(r"(?i)\bCONCILIACION_SALDOS\s*=\s*(?P<formula>[^;]+);")
_PREFIJOS = (
    "SABANA_FINAL_",
    "RESULTADO_",
    "INCONS_DEP_CORREGIDA_",
    "INCONS_DEP_",
)


@dataclass(frozen=True)
class TablaFinal:
    """Una tabla de resultado, con sus columnas en el orden del `SELECT`."""

    tabla: str
    columnas: tuple[str, ...]
    fuente: str
    linea: int

    @property
    def producto(self) -> str:
        """Sufijo del producto (`AHORROS`, `CTE`, `NEQUI`) segun el nombre de la tabla."""
        for prefijo in _PREFIJOS:
            if self.tabla.upper().startswith(prefijo):
                return self.tabla[len(prefijo) :]
        return ""


@dataclass(frozen=True)
class Exportacion:
    """Un `PROC EXPORT` del programa: dataset de origen, archivo y delimitador."""

    dataset: str
    archivo: str
    delimitador: str
    reemplaza: bool
    linea: int

    @property
    def nombre(self) -> str:
        """Nombre del archivo, sin la carpeta de origen."""
        return Path(self.archivo.replace("\\", "/")).name


def tablas_finales(texto: str) -> list[TablaFinal]:
    """Tablas de resultado del programa, sin repetir y en orden de aparicion."""
    vistas: set[str] = set()
    resultado: list[TablaFinal] = []
    for desplazamiento, sentencia in _partir(texto)[1]:
        crear = _CREATE.search(sentencia)
        if crear is None:
            continue
        tabla = crear.group("tabla")
        if not tabla.upper().startswith(_PREFIJOS) or tabla.casefold() in vistas:
            continue
        vistas.add(tabla.casefold())
        unido = _JOIN.search(sentencia)
        linea = texto.count("\n", 0, desplazamiento) + sentencia.count("\n", 0, crear.start()) + 1
        resultado.append(
            TablaFinal(
                tabla=tabla,
                columnas=_columnas(crear.group("lista")),
                fuente=unido.group("fuente") if unido else "",
                linea=linea,
            )
        )
    return resultado


def exportaciones(texto: str) -> list[Exportacion]:
    """`PROC EXPORT` del programa, con el archivo y el delimitador que declara cada uno."""
    resultado: list[Exportacion] = []
    for m in _EXPORT.finditer(texto):
        # En el SAS, `delimiter=';'` va en una sentencia aparte despues del `;` del PROC EXPORT.
        delimitador = _DELIMITADOR.search(texto[m.end() : m.end() + 160])
        resultado.append(
            Exportacion(
                dataset=m.group("dataset"),
                archivo=m.group("archivo"),
                delimitador=delimitador.group("delim") if delimitador else "",
                reemplaza=bool(_REPLACE.search(m.group("resto"))),
                linea=texto.count("\n", 0, m.start()) + 1,
            )
        )
    return resultado


def formula_conciliacion(texto: str) -> str | None:
    """Formula de conciliacion de saldos que el SAS calcula, sin espacios sobrantes."""
    m = _CONCILIACION.search(texto)
    return re.sub(r"\s+", "", m.group("formula")) if m else None


def _columnas(lista: str) -> tuple[str, ...]:
    """Columnas de la lista del `SELECT`, en orden, sin alias ni repetidas."""
    vistos: set[str] = set()
    columnas: list[str] = []
    for trozo in lista.split(","):
        m = _COLUMNA.search(trozo.strip())
        if m is None:
            continue
        nombre = m.group("literal") or m.group("nombre")
        if nombre.casefold() in vistos:
            continue
        vistos.add(nombre.casefold())
        columnas.append(nombre)
    return tuple(columnas)
