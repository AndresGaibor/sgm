"""R1-05: la regla de ubicación del caso v03 como expresiones Java del `tMap` de ubicación.

La regla sale de `proceso.reglas_ubicacion`. Cada alternativa del `WHERE` y cada rama del `CASE` es
una expresión; el rechazo es su unión y el válido su negación. Las funciones de SAS que el oráculo
SQL no cubre se traducen así (ninguna depende de rutinas de Studio):

* **Texto sin blancos finales** (`recortado`): `expr.replaceAll(" +$", "")`. En SAS los blancos
  finales no cuentan en una comparación, así que `'900 '` es igual a `'900'`. Un nulo es `""`.
* **Faltante** (`faltante`): el texto sin blancos finales está vacío. En SAS un texto en blanco
  ES faltante, y el faltante es igual a `''`.
* **LENGTH** (`longitud`): `LENGTH` no cuenta blancos finales, y un texto en blanco tiene longitud
  1 (igual que el faltante). Con `recortado`: `t.isEmpty() ? 1 : t.length()`.
* **CONTAINS** (`mayusculas` + `.contains`): subcadena literal. `UPPER` pasa a mayúsculas con
  `Locale.ROOT`, así que `'Sin Dir'` y `'SIN DIR'` cuentan igual. Un blanco doble (`'SIN  DIR'`)
  no contiene `'SIN DIR'`: ninguna compresión de blancos se aplica (no hay `COMPBL` en el caso).
* **Literal a la izquierda** en cada `equals`: `"900".equals(...)`. Con el lookup, `ubic_pais` y
  `ubic_dane` son nulos cuando no hay pareja; `== null` sobre la columna del lookup es seguro.

Motivos (en orden del `CASE`): país sin pareja, DANE sin pareja para el país `900`, código con país
distinto de `900`, y dirección. Los motivos vienen del SAS, no se escriben aquí.
"""

from __future__ import annotations

from sgm.proceso.reglas_ubicacion import INCONSISTENCIA, ReglaUbicacion
from sgm.talend_item.modelo import Columna
from sgm.talend_item.normalizacion import literal_java
from sgm.talend_item.tmap import SalidaMap

ENTRADA = "ubic_fuente"  # la sábana del producto, que llega de tReplicate_1
LOOKUP_PAIS = "ubic_pais"  # LEFT JOIN contra Cod_pais.xlsx por PAIS
LOOKUP_DANE = "ubic_dane"  # LEFT JOIN contra CODIGOS_DANE.xlsx por CODIGO_UBICACION
SALIDAS = {"rechazo": "ubic_rechazo", "valida": "ubic_valida"}
DIRECCION = "DIRECCION"


def recortado(expresion: str) -> str:
    """Texto sin blancos finales; un nulo da cadena vacía (igual que el faltante de SAS)."""
    return f'({expresion} == null ? "" : {expresion}.replaceAll(" +$", ""))'


def faltante(columna: str, fila: str = ENTRADA) -> str:
    """El campo es faltante de SAS: en blanco o solo con blancos."""
    return f"{recortado(f'{fila}.{columna}')}.isEmpty()"


def longitud(columna: str, fila: str = ENTRADA) -> str:
    """`LENGTH()` de SAS: sin blancos finales, y 1 para un texto en blanco."""
    texto = recortado(f"{fila}.{columna}")
    return f"({texto}.isEmpty() ? 1 : {texto}.length())"


def mayusculas(columna: str, fila: str = ENTRADA) -> str:
    """`UPPER()` de SAS con configuración regional neutra."""
    return f"{recortado(f'{fila}.{columna}')}.toUpperCase(java.util.Locale.ROOT)"


def clave_pais(fila: str = ENTRADA) -> str:
    """Expresión de la unión con Cod_pais: el PAIS sin blancos finales."""
    return recortado(f"{fila}.PAIS")


def clave_dane(fila: str = ENTRADA) -> str:
    """Expresión de la unión con CODIGOS_DANE: el CODIGO_UBICACION sin blancos finales."""
    return recortado(f"{fila}.CODIGO_UBICACION")


def alternativas(regla: ReglaUbicacion, fila: str = ENTRADA) -> dict[str, str]:
    """Las cinco alternativas del `WHERE` como expresiones booleanas, por su clase."""
    pais = recortado(f"{fila}.PAIS")
    literal = literal_java(regla.literal_pais)
    return {
        "pais": f"({LOOKUP_PAIS}.{regla.columna_pais} == null)",
        "dane": f"({literal}.equals({pais}) && {LOOKUP_DANE}.{regla.columna_dane} == null)",
        "extranjera": (
            f"(!{literal}.equals({pais}) && !{faltante('CODIGO_UBICACION', fila)})"
        ),
        "longitud": f"({longitud(DIRECCION, fila)} < {regla.longitud_minima})",
        "fragmento": (
            f"({mayusculas(DIRECCION, fila)}.contains({literal_java(regla.fragmento.upper())}))"
        ),
    }


def rechazo(regla: ReglaUbicacion, fila: str = ENTRADA) -> str:
    """Condición de `INCONS_UBICACION_<P>`: la unión de las cinco alternativas."""
    atomos = alternativas(regla, fila)
    orden = ("pais", "dane", "extranjera", "longitud", "fragmento")
    return "(" + " || ".join(atomos[k] for k in orden) + ")"


def motivo(regla: ReglaUbicacion, fila: str = ENTRADA) -> str:
    """El `CASE` de SAS: la primera rama que se cumple pone su motivo, si no, el de dirección."""
    atomos = alternativas(regla, fila)
    return (
        f"{atomos['pais']} ? {literal_java(regla.motivo_pais)} : "
        f"{atomos['dane']} ? {literal_java(regla.motivo_dane)} : "
        f"{atomos['extranjera']} ? {literal_java(regla.motivo_extranjera)} : "
        f"{literal_java(regla.motivo_direccion)}"
    )


def salidas(regla: ReglaUbicacion, fila: str = ENTRADA) -> list[SalidaMap]:
    """Dos salidas: el rechazo con su `INCONSISTENCIA` y la válida, que es la negación."""
    if not regla.proyeccion_rechazo or not regla.proyeccion_valida:
        raise ValueError("El SAS no proyecta columnas para la ubicación")
    if regla.proyeccion_rechazo[-1] != INCONSISTENCIA:
        raise ValueError("El rechazo de ubicación debe terminar en INCONSISTENCIA")
    condicion = rechazo(regla, fila)
    expresiones_rechazo = {c: f"{fila}.{c}" for c in regla.proyeccion_rechazo[:-1]}
    expresiones_rechazo[INCONSISTENCIA] = f"({motivo(regla, fila)})"
    expresiones_valida = {c: f"{fila}.{c}" for c in regla.proyeccion_valida}
    return [
        SalidaMap(
            SALIDAS["rechazo"],
            [Columna(c) for c in regla.proyeccion_rechazo],
            expresiones_rechazo,
            filtro=condicion,
        ),
        SalidaMap(
            SALIDAS["valida"],
            [Columna(c) for c in regla.proyeccion_valida],
            expresiones_valida,
            filtro=f"!{condicion}",
        ),
    ]


__all__ = [
    "ENTRADA",
    "LOOKUP_DANE",
    "LOOKUP_PAIS",
    "SALIDAS",
    "alternativas",
    "clave_dane",
    "clave_pais",
    "faltante",
    "longitud",
    "motivo",
    "rechazo",
    "recortado",
    "salidas",
]
