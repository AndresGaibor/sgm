"""Agrupa transformaciones hermanas con igual proyección en un solo `tMap` con varias salidas."""

from __future__ import annotations

import copy
import json

from sgm.ir.models import Edge, Operator, Plan
from sgm.optimizar.sustituir import sustituir


def _identidad_entrada(plan: Plan, arista: Edge) -> tuple[str, str]:
    """Identidad de una entrada; dos lecturas puras del mismo dataset equivalen como origen."""
    origen = plan.graph.operator(arista.src)
    if origen.kind == "read":
        params = {k: v for k, v in origen.params.items() if k != "outputs"}
        return "read", json.dumps([params, arista.dataset.lower()], sort_keys=True, default=str)
    return "operator", arista.src


def _forma_rama(op: Operator) -> tuple[str, list[dict], dict] | None:
    """Clave común, pasos que se comparten y filtro propio de una rama."""
    if op.kind != "map" or op.params.get("branches") or op.status == "hueco":
        return None
    pasos = op.params.get("steps") or []
    filtros = [paso for paso in pasos if paso.get("kind") == "filter"]
    if len(filtros) != 1:
        return None
    compartidos = [copy.deepcopy(paso) for paso in pasos if paso.get("kind") != "filter"]
    if not compartidos or any(paso.get("kind") != "derive" for paso in compartidos):
        return None
    if any((paso.get("params") or {}).get("modo") == "agrega" for paso in compartidos):
        return None
    for paso in compartidos:
        (paso.get("params") or {}).pop("outputs", None)
    clave = json.dumps(compartidos, sort_keys=True, ensure_ascii=False, default=str)
    return clave, copy.deepcopy(compartidos), copy.deepcopy(filtros[0])


def _filtro_sobre_salida(filtro: dict, pasos: list[dict]) -> bool:
    """Solo mueve un filtro después de una proyección si sus columnas pasan intactas."""
    identidades = {
        str(asignacion.get("target") or "").strip().lower()
        for paso in pasos
        for asignacion in (paso.get("params") or {}).get("assignments") or []
        if str(asignacion.get("target") or "").strip().lower()
        == str(asignacion.get("expression") or "").strip().lower()
    }
    usadas: set[str] = set()
    expresion = str((filtro.get("params") or {}).get("expression") or "")

    def recopilar(partes: list[str]) -> None:
        usadas.add(partes[-1].lower())
        return None

    sustituir(expresion, recopilar)
    return bool(usadas) and usadas <= identidades


def unir_ramas_hermanas(plan: Plan) -> list[tuple[str, str, list[str]]]:
    """Une mapas hermanos con una entrada común y proyección idéntica.

    Devuelve `(id_conservado, tabla_entrada, ids_absorbidos)`. No combina filtros ni
    proyecciones distintos: cada salida debe tener exactamente el mismo esquema y expresiones.
    """
    grafo = plan.graph
    grupos: dict[
        tuple[tuple[str, str], str],
        list[tuple[Operator, list[Edge], list[dict], dict]],
    ] = {}
    for op_id in grafo.topological():
        op = grafo.operator(op_id)
        forma = _forma_rama(op)
        if forma is None:
            continue
        clave, pasos, filtro = forma
        if not _filtro_sobre_salida(filtro, pasos):
            continue
        entradas = grafo.in_edges(op_id)
        if len(entradas) != 1:
            continue
        arista = entradas[0]
        grupos.setdefault((_identidad_entrada(plan, arista), clave), []).append(
            (op, entradas, pasos, filtro)
        )

    unidos: list[tuple[str, str, list[str]]] = []
    for (_, _), miembros in grupos.items():
        if len(miembros) < 2:
            continue
        arista_entrada = miembros[0][1][0]
        productor = grafo.operator(arista_entrada.src)
        tabla = str(productor.params.get("dataset") or arista_entrada.dataset)
        # Todas las ramas tienen una salida distinta y llegan a la misma fuente.
        salidas = [str((op.params.get("outputs") or [""])[0]) for op, *_ in miembros]
        if any(
            entradas[0].dataset != arista_entrada.dataset for _, entradas, _, _ in miembros
        ):
            continue
        repetidas = len({salida.lower() for salida in salidas}) != len(salidas)
        if any(not salida for salida in salidas) or repetidas:
            continue
        conservado = miembros[0][0]
        origen = arista_entrada.src
        absorbidos: list[str] = []
        for op, entradas, _, _ in miembros[1:]:
            if entradas[0].src != origen:
                grafo.rewire_inputs(
                    op.id,
                    [Edge(origen, op.id, entradas[0].dataset, entradas[0].materialize)],
                )
        ramas = [
            {"expression": filtro["params"].get("expression", ""), "outputs": [salida]}
            for (_, _, _, filtro), salida in zip(miembros, salidas, strict=True)
        ]
        pasos = copy.deepcopy(miembros[0][2])
        conservado.kind = "map"
        conservado.params = {"steps": pasos, "outputs": salidas, "branches": ramas}
        for op, _, _, _ in miembros[1:]:
            for arista in grafo.out_edges(op.id):
                grafo.add_edge(Edge(conservado.id, arista.dst, arista.dataset, arista.materialize))
            absorbidos.append(op.id)
            grafo.remove_operator(op.id)
        for _, entradas, _, _ in miembros[1:]:
            otro_origen = entradas[0].src
            if otro_origen != origen and otro_origen in grafo and not grafo.successors(otro_origen):
                absorbidos.append(otro_origen)
                grafo.remove_operator(otro_origen)
        unidos.append((conservado.id, tabla, absorbidos))
    return unidos


__all__ = ["unir_ramas_hermanas"]
