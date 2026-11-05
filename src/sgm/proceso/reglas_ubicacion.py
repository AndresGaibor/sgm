"""R1-05: la regla de ubicación que el SAS demuestra, leída del caso `v03_pais_dane`.

El caso importa dos Excel de homologación (`Cod_pais.xlsx` y `CODIGOS_DANE.xlsx`) y une la sábana de
cada producto con ellos por `LEFT JOIN`. El rechazo es un `WHERE` de cinco alternativas y un `CASE`
que pone el motivo; los válidos son las filas que no están en el rechazo (`NOT IN` por llave). Cada
pieza se busca por su forma: si el programa cambia una, falla con `ValueError` y no se emite nada a
medias. Las macros se expanden con `reglas_saldo.expandir_macros`.

Pendientes que este lector publica y no resuelve:

* `Codigo_Pais` pasa por `COMPRESS(input(left(...), 10.))`. Ese `input()` quita ceros a la izquierda
  (`01` queda `1`). El Job compara como texto; el caso no tiene códigos con ceros.
* El `CASE` de PROC SQL fija la longitud de `INCONSISTENCIA` con su primera rama. El caso no lo
  ejecutó SAS; el Job no trunca.
* La unión `SABANA_UBIC` (LEFT JOIN por `LLAVE_NOMBRE`) no está en el Job: R1-02 deja
  `LLAVE_NOMBRE` vacía (hito 85). El arnés une los CSV antes de entregárselos al Job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.reglas_saldo import expandir_macros
from sgm.proceso.reglas_ubicacion_forma import (
    COLUMNAS_BASE,
    DANE_FORMATO,
    INCONSISTENCIA,
    PAIS_IMPORT,
    RECHAZO,
    VALIDA,
    forma_producto,
)

_CREAR = re.compile(r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<tabla>\w+)\s+AS\s+(?P<cuerpo>.*?);")
_IMPORTA = re.compile(
    r"(?is)PROC\s+IMPORT\s+DATAFILE\s*=\s*'[^']*?(?P<archivo>[^\\/']+\.xlsx)'\s+"
    r"DBMS\s*=\s*EXCELCS\s+OUT\s*=\s*(?:WORK\.)?(?P<tabla>\w+)"
)
_COMPRESS = re.compile(r"(?is)Codigo_Pais\s*=\s*COMPRESS\(\s*input\(\s*left\(")
_DANE_SELECT = re.compile(r"(?is)SELECT\s+\w+\.(?P<col>\w+)\s+FROM\s+WORK\.(?P<tabla>\w+)")


@dataclass(frozen=True)
class ReglaUbicacion:
    """Lo que el caso demuestra para rechazar ubicaciones, igual en todos los productos."""

    productos: tuple[str, ...]
    literal_pais: str  # '900': el país que lleva DANE
    longitud_minima: int  # 8: `LENGTH(DIRECCION) < 8`
    fragmento: str  # 'sin dir', en minúsculas como en el SAS
    motivo_pais: str
    motivo_dane: str
    motivo_extranjera: str
    motivo_direccion: str
    archivo_pais: str  # Cod_pais.xlsx
    columna_pais: str  # Codigo_Pais, la columna del Excel que se une con PAIS
    archivo_dane: str  # CODIGOS_DANE.xlsx
    columna_dane: str  # CODIGO_DANE
    proyeccion_rechazo: tuple[str, ...]  # columnas de INCONS_UBICACION_<P>, con INCONSISTENCIA
    proyeccion_valida: tuple[str, ...]  # columnas de UBIC_VALIDA_<P>
    llave: str  # LLAVE_NOMBRE: la llave del NOT IN de los válidos
    pendientes: tuple[str, ...] = ()


def _tablas(texto: str) -> dict[str, str]:
    """Cuerpo de cada `CREATE TABLE` por nombre. Un rechazo o un válido repetido es error."""
    tablas: dict[str, str] = {}
    for crear in _CREAR.finditer(texto):
        nombre = crear.group("tabla").upper()
        if nombre in tablas and nombre.startswith((RECHAZO, VALIDA)):
            raise ValueError(f"El SAS crea dos veces la tabla {nombre}")
        tablas[nombre] = crear.group("cuerpo")
    return tablas


def _excel(texto: str) -> dict[str, str]:
    """Archivo `.xlsx` que importa cada `PROC IMPORT ... OUT=WORK.<tabla>`."""
    return {m.group("tabla").upper(): m.group("archivo") for m in _IMPORTA.finditer(texto)}


def reglas_ubicacion(texto: str) -> ReglaUbicacion:
    """La regla de ubicación del programa. Falla con `ValueError` si falta una pieza o difiere."""
    expandido = expandir_macros(texto)
    tablas = _tablas(expandido)
    productos = sorted({n[len(RECHAZO) :] for n in tablas if n.startswith(RECHAZO)})
    if not productos:
        raise ValueError(f"El SAS no declara ninguna tabla {RECHAZO}<producto>")
    excel = _excel(expandido)
    if PAIS_IMPORT not in excel or DANE_FORMATO not in tablas:
        raise ValueError("Falta el Excel de país o la tabla de formato de DANE")
    dane = _DANE_SELECT.search(tablas[DANE_FORMATO])
    if dane is None or dane.group("col").upper() != "CODIGO_DANE":
        raise ValueError(f"{DANE_FORMATO} no proyecta CODIGO_DANE")
    if dane.group("tabla").upper() not in excel:
        raise ValueError(f"El Excel de {dane.group('tabla')} no está importado")
    formas = {p: forma_producto(expandido, tablas, p) for p in productos}
    forma = formas[productos[0]]
    if any(f != forma for f in formas.values()):
        raise ValueError(f"Los productos declaran reglas de ubicación distintas: {productos}")
    literal, longitud, fragmento, motivos, col_pais, col_dane, rechazo, valida, llave = forma
    pendientes = [
        "R1-05: `Codigo_Pais` pasa por `input()` y quita ceros a la izquierda; el Job compara como "
        "texto (sin códigos con ceros en el caso)",
        "R1-05: el `CASE` de PROC SQL fija la longitud de INCONSISTENCIA con su primera "
        "rama; el SAS del caso no se ejecutó, y el Job no trunca",
        f"R1-05: la unión SABANA_UBIC por {llave} no está en el Job; R1-02 deja la llave vacía",
    ]
    if not _COMPRESS.search(expandido):
        pendientes.pop(0)
    return ReglaUbicacion(
        productos=tuple(productos),
        literal_pais=literal,
        longitud_minima=longitud,
        fragmento=fragmento,
        motivo_pais=motivos[0],
        motivo_dane=motivos[1],
        motivo_extranjera=motivos[2],
        motivo_direccion=motivos[3],
        archivo_pais=excel[PAIS_IMPORT],
        columna_pais=col_pais,
        archivo_dane=excel[dane.group("tabla").upper()],
        columna_dane=col_dane,
        proyeccion_rechazo=rechazo,
        proyeccion_valida=valida,
        llave=llave,
        pendientes=tuple(pendientes),
    )


__all__ = ["COLUMNAS_BASE", "INCONSISTENCIA", "ReglaUbicacion", "reglas_ubicacion"]
