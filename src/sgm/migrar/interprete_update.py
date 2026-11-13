"""`UPDATE` de un DATA step: aplica una transacción a un maestro, una observación por grupo BY.

Semántica de `lrcon` (pp. 604 a 609): cada llave del maestro sale una vez. La transacción se
aplica a la primera observación del maestro con esa llave. Los valores faltantes de la
transacción no la sobrescriben (p. 604), y una llave que solo está en la transacción se agrega
(p. 604). Un maestro con llave repetida conserva sus demás observaciones sin tocar (ejemplo 2,
p. 608). `UPDATEMODE=NOMISSINGCHECK` no tiene caso todavía: queda como pendiente `P-UPDATEMODE`.
"""

from __future__ import annotations

from sgm.migrar.interprete_base import _clave
from sgm.migrar.interprete_valores import NoSoportadoEnInterprete, _columna


def _faltante(valor: object) -> bool:
    return valor is None or valor == ""


def _agrupar(filas: list[dict], llaves: list[str]) -> dict[tuple, list[dict]]:
    grupos: dict[tuple, list[dict]] = {}
    for fila in filas:
        clave = tuple(_clave(_columna(fila, k)) for k in llaves)
        grupos.setdefault(clave, []).append(fila)
    return grupos


def _actualizar(entradas: list[list[dict]], params: dict) -> list[dict]:
    """`entradas[0]` es el maestro y `entradas[1]` la transacción de `UPDATE maestro trans;`."""
    if params.get("updatemode"):
        raise NoSoportadoEnInterprete(
            "update", "UPDATEMODE=NOMISSINGCHECK sin soporte (P-UPDATEMODE)"
        )
    llaves = [str(n).split(".")[-1].lower() for n in params.get("by") or []]
    if not llaves:
        raise NoSoportadoEnInterprete("update", "UPDATE sin BY")
    if len(entradas) != 2:
        raise NoSoportadoEnInterprete(
            "update", "más de una tabla de transacción: el orden no está verificado"
        )
    for filas in entradas:
        claves = [tuple(_clave(_columna(f, k)) for k in llaves) for f in filas]
        if any(antes > despues for antes, despues in zip(claves, claves[1:], strict=False)):
            raise NoSoportadoEnInterprete("update", "entrada no ordenada por BY (lrcon, p. 605)")
    maestro, transaccion = entradas
    grupos_m = _agrupar(maestro, llaves)
    grupos_t = _agrupar(transaccion, llaves)
    columnas: list[str] = []
    for fila in [*maestro[:1], *transaccion[:1]]:
        columnas += [c for c in fila if c not in columnas]
    salida: list[dict] = []
    for llave in sorted(set(grupos_m) | set(grupos_t)):
        filas_m = grupos_m.get(llave, [])
        trans = grupos_t.get(llave, [])
        if filas_m:
            primera = dict(filas_m[0])
            for fila in trans:
                primera.update({c: v for c, v in fila.items() if not _faltante(v)})
            salida += [primera, *(dict(f) for f in filas_m[1:])]
        else:
            # Llave nueva: la primera transacción entra entera; las demás solo aportan no faltantes.
            primera = dict(trans[0])
            for fila in trans[1:]:
                primera.update({c: v for c, v in fila.items() if not _faltante(v)})
            salida.append(primera)
    return [{c: fila.get(c) for c in columnas} for fila in salida]
