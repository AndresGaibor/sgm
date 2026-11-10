"""Un mismo cálculo escrito dos veces en el SAS se hace una sola vez en el Job.

En SAS es normal repetir una subconsulta en dos sentencias, o leer la misma tabla y agruparla igual
en tres `PROC SQL`. Traducido tal cual, el Job lee el archivo tres veces y agrupa tres veces. Una
persona lo calcula una vez y reparte el resultado.

Dos operadores son el mismo cálculo cuando tienen el mismo tipo, los mismos parámetros (sin contar
el nombre que el SAS le dio al resultado) y exactamente las mismas entradas. Se unen de arriba
abajo: al unir dos lecturas, los pasos que las siguen pasan a tener la misma entrada y se pueden
unir también.

No se unen dos operadores cuyos resultados se vuelven a juntar más abajo (un cruce de una tabla
consigo misma, una unión de dos ramas): en Talend un flujo repartido no puede volver a encontrarse
en el mismo componente, y ahí cada rama necesita su propia lectura.
"""

from __future__ import annotations

import json
import re

from sgm.ir.models import Edge, Operator, Plan

UNIBLES = frozenset(
    {"read", "map", "filter", "derive", "select", "rename", "join", "sort", "dedup", "aggregate"}
)


def _sin_nombre(valor: object) -> object:
    """Los parámetros sin el nombre del resultado, que no cambia lo que se calcula."""
    if isinstance(valor, dict):
        return {k: _sin_nombre(v) for k, v in valor.items() if k != "outputs"}
    if isinstance(valor, list):
        return [_sin_nombre(v) for v in valor]
    return valor


def _clave(plan: Plan, op: Operator) -> str | None:
    if op.kind not in UNIBLES or op.status == "hueco" or op.params.get("branches"):
        return None
    entradas = [(e.src, e.dataset.lower()) for e in plan.graph.in_edges(op.id)]
    if not entradas:
        return None
    cuerpo = json.dumps(_sin_nombre(op.params), sort_keys=True, default=str, ensure_ascii=False)
    return json.dumps([op.kind, op.placement, cuerpo, sorted(set(entradas))])


def _renombrar(valor: object, viejo: str, nuevo: str) -> object:
    """Cambia el nombre de una tabla donde aparezca: como conjunto o calificando columnas."""
    if isinstance(valor, dict):
        return {k: _renombrar(v, viejo, nuevo) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_renombrar(v, viejo, nuevo) for v in valor]
    if not isinstance(valor, str):
        return valor
    tabla_vieja, tabla_nueva = viejo.split(".")[-1], nuevo.split(".")[-1]
    if valor.strip().lower() in (viejo.lower(), tabla_vieja.lower()):
        return nuevo if "." in valor else tabla_nueva
    return re.sub(
        rf"(?i)(?<![\w.]){re.escape(tabla_vieja)}\.(?=[A-Za-z_*])", f"{tabla_nueva}.", valor
    )


def _unir(plan: Plan, queda: Operator, sobra: Operator) -> None:
    grafo = plan.graph
    nombres_queda = list(queda.params.get("outputs") or [])
    nombres_sobra = list(sobra.params.get("outputs") or [])
    if nombres_sobra and not nombres_queda:
        queda.params["outputs"] = nombres_sobra
        pasos = queda.params.get("steps") or []
        if pasos and "outputs" in (sobra.params.get("steps") or [{}])[-1].get("params", {}):
            pasos[-1].setdefault("params", {})["outputs"] = nombres_sobra
    elif nombres_sobra and nombres_queda:
        viejo, nuevo = str(nombres_sobra[0]), str(nombres_queda[0])
        if viejo.lower() != nuevo.lower():
            for op in grafo.operators():
                if op.id not in (queda.id, sobra.id):
                    op.params = _renombrar(op.params, viejo, nuevo)
    destino = str((queda.params.get("outputs") or [""])[0])
    for arista in grafo.out_edges(sobra.id):
        dataset = arista.dataset
        if nombres_sobra and dataset.lower() == str(nombres_sobra[0]).lower() and destino:
            dataset = destino
        grafo.add_edge(Edge(queda.id, arista.dst, dataset, arista.materialize))
    queda.inherit_expression_evidence(sobra)
    queda.evidence += [ev for ev in sobra.evidence if ev not in queda.evidence]
    grafo.remove_operator(sobra.id)


def unir_duplicados(plan: Plan) -> list[tuple[str, str]]:
    """Une cada operador repetido con el primero igual a él. Devuelve los pares `(sobra, queda)`."""
    grafo = plan.graph
    unidos: list[tuple[str, str]] = []
    vistos: dict[str, str] = {}
    # Una sola pasada en orden de flujo: al llegar a un operador, sus entradas ya están unidas.
    for op_id in grafo.topological():
        clave = _clave(plan, grafo.operator(op_id))
        if clave is None:
            continue
        primero = vistos.setdefault(clave, op_id)
        if primero == op_id or grafo.descendants(primero) & grafo.descendants(op_id):
            continue
        _unir(plan, grafo.operator(primero), grafo.operator(op_id))
        unidos.append((op_id, primero))
    return unidos


__all__ = ["UNIBLES", "unir_duplicados"]
