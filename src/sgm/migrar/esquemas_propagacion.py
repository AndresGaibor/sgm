"""Propagación de tipos por el plan lógico, operador a operador, con su fuente (B-3).

Reglas con página en la guía SAS (ver `docs/referencia/sas/`):
- `LENGTH x $8` declara carácter de largo 8 (`lrcon`, p. 68 y 73; fuente `LENGTH`).
- Una asignación con aritmética da numérico aunque la entrada no tenga tipo demostrado; esa entrada
  queda pendiente `P-TIPO-DESCONOCIDO` (`lrcon`, «Variable Type Conversions», p. 75).
- `SET a b`: si una variable tiene tipos distintos en sus orígenes, es `P-UNION-TIPO-CONFLICTO`
  con ambos (`lestmtsref`, «SET Statement», p. 343).
- `COUNT` y las demás funciones numéricas de `PROC SQL` dan numérico (`sqlproc`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.ir.models import Operator, Plan
from sgm.migrar.esquemas import PendienteMigracion

NUMERICO = "numerico"
CARACTER = "caracter"

_CADENA = re.compile(r"'[^']*'|\"[^\"]*\"")
_IDENTIFICADOR = re.compile(r"(?<![\w.])[A-Za-z_]\w*(?:\.\w+)?\b(?!\s*\()")
_NUMERO = re.compile(r"-?\d+(?:\.\d+)?")
_OPERADOR = re.compile(r"[+\-*/]")
_LLAMADA_NUMERICA = re.compile(
    r"\s*(count|n|sum|mean|avg|round|abs|int|floor|ceil|sqrt|exp|log|nmiss|min|max)\s*\(",
    re.IGNORECASE,
)
_PALABRAS = frozenset({"and", "or", "not", "if", "then", "else", "end", "when", "case", "missing"})


@dataclass(frozen=True)
class TipoColumna:
    nombre: str
    tipo: str | None  # numerico, caracter o None si no hay demostración
    largo: int | None = None
    fuente: str = ""
    linea: int | None = None  # línea del SAS del operador que la define


@dataclass(frozen=True)
class ResultadoTipos:
    tablas: dict[str, dict[str, TipoColumna]]  # conjunto (minúsculas) -> columnas
    pendientes: list[PendienteMigracion]


def _sin_cadenas(expresion: str) -> str:
    return _CADENA.sub("''", expresion)


def _identificadores(expresion: str) -> list[str]:
    nombres = [m.group(0).lower() for m in _IDENTIFICADOR.finditer(_sin_cadenas(expresion))]
    return [n for n in nombres if n not in _PALABRAS]


def _tipo_de_asignacion(
    expresion: str, entrada: dict[str, TipoColumna]
) -> tuple[str | None, list[str]]:
    """Tipo que demuestra la expresión y las entradas que le faltan para demostrarlo."""
    texto = expresion.strip()
    if _CADENA.fullmatch(texto):
        return CARACTER, []
    if _NUMERO.fullmatch(texto) or _LLAMADA_NUMERICA.match(texto):
        return NUMERICO, []
    faltan = [n for n in _identificadores(texto) if n not in entrada]
    if _OPERADOR.search(_sin_cadenas(texto)):
        return NUMERICO, faltan
    if texto.lower() in entrada:
        return entrada[texto.lower()].tipo, []
    return None, faltan


def _mezclar(listas: list[dict[str, TipoColumna]]) -> dict[str, TipoColumna]:
    """Columnas de varias entradas; si dos la definen, gana la primera."""
    merged: dict[str, TipoColumna] = {}
    for lista in listas:
        for nombre, columna in lista.items():
            merged.setdefault(nombre, columna)
    return merged


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _conjunto(op: Operator) -> str:
    if op.kind == "read":
        return str(op.params.get("dataset") or "").lower()
    salidas = op.params.get("outputs") or []
    return str(salidas[0]).lower() if salidas else op.id


def propagar_tipos(plan: Plan) -> ResultadoTipos:
    """Recorre el plan en orden y devuelve las columnas de cada conjunto con su fuente."""
    grafo = plan.graph
    resultados: dict[str, dict[str, TipoColumna]] = {}
    tablas: dict[str, dict[str, TipoColumna]] = {}
    pendientes: list[PendienteMigracion] = []

    def procesar(op_id: str) -> None:
        if op_id in resultados:
            return
        preds = list(grafo.predecessors(op_id))
        for previo in preds:
            procesar(previo)
        op = grafo.operator(op_id)
        if op.kind == "read":
            resultado = dict(tablas.get(_conjunto(op), {}))
        elif op.kind == "derive":
            resultado = _derivar(op, _mezclar([resultados[p] for p in preds]), pendientes)
        elif op.kind == "union":
            fuentes = [(_conjunto(grafo.operator(p)), resultados[p]) for p in preds]
            resultado = _unir(fuentes, pendientes)
        elif op.kind == "aggregate":
            resultado = _agregar(op, _mezclar([resultados[p] for p in preds]))
        else:
            resultado = _mezclar([resultados[p] for p in preds])
        resultados[op_id] = resultado
        for salida in op.params.get("outputs") or []:
            tablas[str(salida).lower()] = resultado

    for op in grafo.operators():
        procesar(op.id)
    return ResultadoTipos(tablas=tablas, pendientes=pendientes)


def _derivar(
    op: Operator, entrada: dict[str, TipoColumna], pendientes: list[PendienteMigracion]
) -> dict[str, TipoColumna]:
    salida = dict(entrada)
    declarados = op.params.get("declared") or {}
    for asignacion in op.params.get("assignments") or []:
        destino = str(asignacion.get("target", "")).lower()
        expresion = str(asignacion.get("expression", ""))
        if any(nombre.lower() == destino for nombre in declarados):
            tipo, largo = _declarado(declarados, destino)
            salida[destino] = TipoColumna(destino, tipo, largo, "declarado", _linea(op))
            continue
        tipo, faltan = _tipo_de_asignacion(expresion, salida)
        for falta in faltan:
            pendientes.append(
                PendienteMigracion(
                    "P-TIPO-DESCONOCIDO",
                    f"{falta}: se usa en «{expresion}» sin tipo demostrado",
                    None,
                )
            )
        salida[destino] = TipoColumna(destino, tipo, None, "derivada", _linea(op))
    return salida


def _declarado(declarados: dict, destino: str) -> tuple[str | None, int | None]:
    for nombre, valor in declarados.items():
        if nombre.lower() != destino:
            continue
        if isinstance(valor, (list, tuple)):
            tipo = str(valor[0])
            largo = int(valor[1]) if len(valor) > 1 and valor[1] is not None else None
        else:
            tipo, largo = str(valor), None
        return (CARACTER if tipo == "String" else NUMERICO), largo
    return None, None


def _unir(
    fuentes: list[tuple[str, dict[str, TipoColumna]]], pendientes: list[PendienteMigracion]
) -> dict[str, TipoColumna]:
    """`SET a b`: toma el primer tipo demostrado; si las fuentes discrepan, hay conflicto."""
    apariciones: dict[str, list[tuple[str, TipoColumna]]] = {}
    for conjunto, columnas in fuentes:
        for nombre, columna in columnas.items():
            apariciones.setdefault(nombre, []).append((conjunto, columna))
    salida: dict[str, TipoColumna] = {}
    for nombre, lista in apariciones.items():
        demostrados = [(c, col) for c, col in lista if col.tipo is not None]
        if len({col.tipo for _, col in demostrados}) > 1:
            partes = ", ".join(f"{c}={col.tipo}" for c, col in demostrados)
            pendientes.append(
                PendienteMigracion("P-UNION-TIPO-CONFLICTO", f"{nombre}: {partes}", None)
            )
        primera = lista[0][1]
        tipo = demostrados[0][1].tipo if demostrados else None
        salida[nombre] = TipoColumna(nombre, tipo, primera.largo, primera.fuente)
    return salida


def _agregar(op: Operator, entrada: dict[str, TipoColumna]) -> dict[str, TipoColumna]:
    salida: dict[str, TipoColumna] = {}
    for clave in op.params.get("group_by") or []:
        nombre = str(clave).lower()
        if nombre in entrada:
            salida[nombre] = entrada[nombre]
    for agregado in op.params.get("aggregations") or []:
        alias = str(agregado.get("alias", "")).lower()
        tipo, _ = _tipo_de_asignacion(str(agregado.get("expression", "")), entrada)
        salida[alias] = TipoColumna(alias, tipo, None, "agregado", _linea(op))
    return salida


__all__ = ["CARACTER", "NUMERICO", "ResultadoTipos", "TipoColumna", "propagar_tipos"]
