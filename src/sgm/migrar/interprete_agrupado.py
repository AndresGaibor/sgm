"""Agrupación del intérprete: agregados por grupo BY, límites de grupo y `agregar`.

Movido desde `interprete.py` sin cambio de comportamiento (decisión del dueño, hito 242m).
"""

from __future__ import annotations

import re

from sgm.migrar import semantica
from sgm.migrar.interprete_agregados import AgregadoNoSoportado, agregar
from sgm.migrar.interprete_filas import _clave
from sgm.migrar.interprete_valores import (
    NoSoportadoEnInterprete,
    _arbol,
    _columna,
    _numero,
    _valor,
    _verdad,
)

_AGREGADO = re.compile(
    r"^\s*(count|sum|avg|mean|min|max)\s*\(\s*(distinct\s+)?(\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)\s*$",
    re.IGNORECASE,
)


def _calcular(funcion: str, distinto: bool, nombre: str, filas: list[dict]) -> object:
    """Un agregado de `PROC SQL` sobre un grupo: ignora los faltantes; sin valores, es faltante.

    `COUNT(*)` cuenta filas; `COUNT(col)` las no faltantes; `SUM`, `AVG`, `MIN` y `MAX` solo miran
    valores presentes (`sqlproc`, funciones de resumen).
    """
    if nombre == "*":
        return len(filas)
    presentes = [
        valor
        for valor in (_columna(fila, nombre.split(".")[-1]) for fila in filas)
        if not semantica.es_faltante(valor)
    ]
    if funcion == "count":
        return len({_clave(v) for v in presentes}) if distinto else len(presentes)
    if not presentes:
        return None
    if funcion in ("min", "max"):
        elegir = min if funcion == "min" else max
        return elegir(presentes, key=_clave)
    numeros = [n for n in (_numero(v) for v in presentes) if n is not None]
    if not numeros:
        return None
    return sum(numeros) if funcion == "sum" else sum(numeros) / len(numeros)


def _limites(filas: list[dict], llaves: list[str]) -> list[dict]:
    """Por fila, `first.v` y `last.v` de cada variable del `BY` (1 o 0), como el SAS.

    Con varias variables, `first.v` es 1 si cambió `v` o cualquiera de las anteriores.
    """
    claves = [tuple(_clave(_columna(fila, k)) for k in llaves) for fila in filas]
    resultado = []
    for i in range(len(filas)):
        marcas: dict[str, int] = {}
        for k, nombre in enumerate(llaves):
            antes = claves[i - 1][: k + 1] if i else None
            despues = claves[i + 1][: k + 1] if i + 1 < len(filas) else None
            marcas[f"first.{nombre}"] = 1 if antes != claves[i][: k + 1] else 0
            marcas[f"last.{nombre}"] = 1 if despues != claves[i][: k + 1] else 0
        resultado.append(marcas)
    return resultado


def _por_grupo(filas: list[dict], params: dict) -> list[dict]:
    """Programa por fila de un DATA step con `BY`: retención, suma, `FIRST.`/`LAST.` y `IF`.

    Las variables retenidas (las del `RETAIN` y las de una sentencia de suma, que empiezan en 0)
    conservan su valor de una fila a la siguiente; las demás variables nuevas empiezan cada fila en
    faltante. Una fila que no pasa un `IF cond;` no sale, pero lo que dejó en las retenidas queda.
    """
    llaves = [str(n).lower() for n in params.get("by") or []]
    programa = params.get("programa") or []
    retenidas: dict[str, object] = {}
    for paso in programa:
        if paso["op"] == "retain":
            inicial = paso.get("valor")
            valor = None if inicial is None else _valor(_arbol(str(inicial)), {})
            retenidas.update(dict.fromkeys(paso["names"], valor))
        elif paso["op"] == "suma":
            retenidas.setdefault(paso["target"], 0)
    nuevas: list[str] = []
    resultado: list[dict] = []
    for fila, marcas in zip(filas, _limites(filas, llaves), strict=True):
        pdv = {**retenidas, **fila}
        seguir = True
        for paso in programa:
            clase = paso["op"]
            vista = {**pdv, **marcas}
            if clase == "asigna":
                pdv[paso["target"]] = _valor(_arbol(paso["expr"]), vista)
                destino = paso["target"]
            elif clase == "si":
                destino = paso["target"]
                if _verdad(_valor(_arbol(paso["cond"]), vista)):
                    pdv[destino] = _valor(_arbol(paso["expr"]), vista)
            elif clase == "suma":
                destino = paso["target"]
                suma = _numero(_valor(_arbol(paso["expr"]), vista))
                pdv[destino] = (_numero(pdv.get(destino)) or 0) + (suma or 0)
            elif clase == "filtra":
                destino = None
                if not _verdad(_valor(_arbol(paso["cond"]), vista)):
                    seguir = False
            else:
                destino = None
            if destino and destino not in fila and destino not in nuevas:
                nuevas.append(destino)
        for nombre in retenidas:
            if nombre in pdv:
                retenidas[nombre] = pdv[nombre]
            if nombre not in fila and nombre not in nuevas:
                nuevas.append(nombre)
        if seguir:
            resultado.append(pdv)
    columnas = [*(filas[0] if filas else {}), *nuevas]
    return [{c: fila.get(c) for c in columnas} for fila in resultado]


def _agregar(filas: list[dict], params: dict) -> list[dict]:
    """Adapta los agregados compatibles al error público del intérprete."""
    try:
        return agregar(
            filas,
            params,
            parsear=_arbol,
            evaluar=_valor,
            columna=_columna,
            clave=_clave,
        )
    except AgregadoNoSoportado as error:
        raise NoSoportadoEnInterprete("aggregate", str(error)) from error


