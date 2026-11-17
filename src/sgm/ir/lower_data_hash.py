"""Objetos hash e iteradores del DATA step: cada método es un pendiente con su código (B-21).

El lookup `FIND` con tMap (paso a del plan) aún no se traduce: todo objeto hash es un hueco.
Los códigos y sus páginas de `lrcon`:

* `DECLARE HASH` y `FIND`/`CHECK`: `P-HASH-LOOKUP-SIN-SOPORTE` (p. 628 a 634).
* `ADD`, `REF`, `REMOVE`, `REPLACE`: `P-HASH-MUTABLE` (p. 633 y 638).
* `OUTPUT` del objeto hash: `P-HASH-OUTPUT` (p. 639).
* `DECLARE HITER` y sus métodos: `P-HASH-ITERADOR` (p. 642).
* `rc` de un `FIND` usado fuera de la búsqueda traducida: `P-HASH-RC-SIN-SOPORTE` (p. 634).

Los métodos de definición (`DEFINEKEY`, `DEFINEDATA`, `DEFINEDONE`) forman parte de la
declaración del objeto y no llevan código propio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.frontend.datastep import DsStatement

_DECLARA_HASH = re.compile(r"(?i)^declare\s+hash\s+(\w+)")
_DECLARA_HITER = re.compile(r"(?i)^declare\s+hiter\s+(\w+)")
_METODO = re.compile(r"(?i)\b(\w+)\s*\.\s*(\w+)\s*\(")

_DEFINICION = frozenset({"definekey", "definedata", "definedone", "new"})
_MUTABLE = frozenset({"add", "ref", "remove", "replace"})
_BUSQUEDA = frozenset({"find", "check"})
_ITERADOR = frozenset({"first", "last", "next", "prev"})
_RC = re.compile(r"(?i)\brc\b")


@dataclass(frozen=True)
class Pendiente:
    """Un objeto hash o iterador del paso: su sentencia, su código y su motivo."""

    indice: int
    codigo: str
    motivo: str


def _de_metodo(metodo: str, es_iterador: bool) -> tuple[str, str] | None:
    """Código y motivo de un método de objeto hash; None para la declaración (sin código)."""
    m = metodo.lower()
    if m in _DEFINICION:
        return None
    if es_iterador or m in _ITERADOR:
        return "P-HASH-ITERADOR", "iterador del hash (lrcon, p. 642)"
    if m == "output":
        return "P-HASH-OUTPUT", "OUTPUT del objeto hash (lrcon, p. 639)"
    if m in _MUTABLE:
        return "P-HASH-MUTABLE", f"{m} modifica la tabla hash al ejecutar (lrcon, p. 633, 638)"
    if m in _BUSQUEDA:
        return "P-HASH-LOOKUP-SIN-SOPORTE", f"{m} busca en el hash; sin tMap con rc (lrcon, p. 634)"
    return "P-HASH-LOOKUP-SIN-SOPORTE", f"método «{m}» del hash sin equivalencia (lrcon, p. 628)"


def pendientes_hash(stmts: list[DsStatement]) -> list[Pendiente]:
    """Sentencias del paso que usan un objeto hash o iterador, en orden; vacío si no hay ninguno."""
    hashes = {m.group(1).lower() for s in stmts if (m := _DECLARA_HASH.match(s.text.strip()))}
    iteradores = {m.group(1).lower() for s in stmts if (m := _DECLARA_HITER.match(s.text.strip()))}
    if not hashes and not iteradores:
        return []
    salida: list[Pendiente] = []
    for indice, s in enumerate(stmts):
        texto = s.text.strip()
        if m := _DECLARA_HASH.match(texto):
            motivo = f"DECLARE HASH {m.group(1)}: sin lookup con rc (lrcon, p. 629)"
            salida.append(Pendiente(indice, "P-HASH-LOOKUP-SIN-SOPORTE", motivo))
            continue
        if m := _DECLARA_HITER.match(texto):
            motivo = f"DECLARE HITER {m.group(1)}: iterador del hash (lrcon, p. 642)"
            salida.append(Pendiente(indice, "P-HASH-ITERADOR", motivo))
            continue
        for objeto, metodo in _METODO.findall(texto):
            if objeto.lower() not in hashes | iteradores:
                continue
            hallazgo = _de_metodo(metodo, objeto.lower() in iteradores)
            if hallazgo is not None:
                salida.append(Pendiente(indice, hallazgo[0], hallazgo[1]))
                break
    # `rc` fuera de la búsqueda traducida (decisión 6): la sentencia que lo usa queda pendiente.
    marcados = {p.indice for p in salida}
    for indice, s in enumerate(stmts):
        if indice not in marcados and _RC.search(s.text):
            motivo = "rc de FIND: solo se traduce con comparaciones a 0 y DROP rc (lrcon, p. 634)"
            salida.append(Pendiente(indice, "P-HASH-RC-SIN-SOPORTE", motivo))
    return sorted(salida, key=lambda p: p.indice)
