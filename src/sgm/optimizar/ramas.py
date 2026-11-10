"""Agrupa transformaciones hermanas con igual proyección en un solo `tMap` con varias salidas."""

from __future__ import annotations

import copy
import json
import re

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
    if op.kind == "filter" and op.params.get("outputs"):
        filtro = {"params": {"expression": op.params.get("expression", "")}}
        return "[]", [], filtro
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


def _forma_rechazo_union(op: Operator) -> tuple[dict, dict, list[dict], str] | None:
    """Reconoce el patrón demostrado `INNER` frente a `LEFT` + `missing(clave_lookup)`."""
    if op.kind != "map" or op.params.get("branches") or op.status == "hueco":
        return None
    pasos = op.params.get("steps") or []
    uniones = [paso for paso in pasos if paso.get("kind") == "join"]
    filtros = [paso for paso in pasos if paso.get("kind") == "filter"]
    derivaciones = [paso for paso in pasos if paso.get("kind") == "derive"]
    if len(uniones) != 1 or len(filtros) > 1 or len(derivaciones) != 1:
        return None
    union = uniones[0]
    params = union.get("params") or {}
    tipo_union = str(params.get("join_type") or "").lower()
    if tipo_union not in {"inner", "left", "left outer"}:
        return None
    if (tipo_union == "inner" and filtros) or (
        tipo_union in {"left", "left outer"} and not filtros
    ):
        return None
    esperados = ["join", "derive"] if tipo_union == "inner" else ["join", "filter", "derive"]
    if [str(paso.get("kind") or "") for paso in pasos] != esperados:
        return None
    llaves = params.get("keys") or []
    if len(llaves) != 1 or len(llaves[0]) != 2:
        return None
    columna_lookup = str(llaves[0][1]).split(".")[-1]
    if filtros:
        expresion = str((filtros[0].get("params") or {}).get("expression") or "").strip()
        patron = rf"missing\s*\(\s*(?:[a-z_][\w]*\.)?{re.escape(columna_lookup)}\s*\)"
        if not re.fullmatch(patron, expresion, flags=re.IGNORECASE):
            return None
    derivacion = copy.deepcopy(derivaciones[0])
    (derivacion.get("params") or {}).pop("outputs", None)
    return copy.deepcopy(union), copy.deepcopy(derivacion), [union, derivaciones[0]], columna_lookup


def unir_rechazo_inner_hermano(plan: Plan) -> list[tuple[str, str, str, str]]:
    """Combina un INNER y su LEFT+missing equivalente en una salida REJECT del mismo mapa."""
    grafo = plan.graph
    candidatos: dict[tuple, list[tuple[Operator, list[Edge], dict, dict, list[dict], str]]] = {}
    for op_id in grafo.topological():
        op = grafo.operator(op_id)
        forma = _forma_rechazo_union(op)
        if forma is None or len(op.params.get("outputs") or []) != 1:
            continue
        union, derivacion, pasos, columna = forma
        entradas = grafo.in_edges(op_id)
        if len(entradas) != 2:
            continue
        identidad_entradas = tuple(_identidad_entrada(plan, edge) for edge in entradas)
        comparables = copy.deepcopy(union["params"])
        comparables.pop("join_type")
        comparables.pop("interpreter_subquery", None)
        identidad = (
            identidad_entradas,
            json.dumps(comparables, sort_keys=True, ensure_ascii=False, default=str),
            json.dumps(derivacion, sort_keys=True, ensure_ascii=False, default=str),
        )
        candidatos.setdefault(identidad, []).append(
            (op, entradas, union, derivacion, pasos, columna)
        )
    resultado = []
    for miembros in candidatos.values():
        interiores = [
            miembro
            for miembro in miembros
            if str(miembro[2]["params"].get("join_type")).lower() == "inner"
        ]
        izquierdos = [
            miembro
            for miembro in miembros
            if str(miembro[2]["params"].get("join_type")).lower() in {"left", "left outer"}
        ]
        if len(interiores) != 1 or len(izquierdos) != 1:
            continue
        normal, rechazo = interiores[0], izquierdos[0]
        if not rechazo[5] or normal[5].lower() != rechazo[5].lower():
            continue
        salida_normal = normal[0].params["outputs"][0]
        salida_rechazo = rechazo[0].params["outputs"][0]
        if salida_normal.lower() == salida_rechazo.lower():
            continue
        conservado = normal[0]
        conservado.params = {
            "steps": [normal[2], normal[3]],
            "outputs": [salida_normal, salida_rechazo],
            "branches": [
                {"outputs": [salida_normal], "joinKey": normal[5], "matched": True},
                {
                    "outputs": [salida_rechazo],
                    "joinKey": normal[5],
                    "rejectInnerJoin": True,
                },
            ],
        }
        for op, *_ in (rechazo,):
            for edge in grafo.out_edges(op.id):
                grafo.add_edge(Edge(conservado.id, edge.dst, edge.dataset, edge.materialize))
            grafo.remove_operator(op.id)
        resultado.append((conservado.id, rechazo[0].id, salida_normal, salida_rechazo))
    return resultado


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
        if pasos and not _filtro_sobre_salida(filtro, pasos):
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
        tabla = str(
            productor.params.get("dataset")
            or next(iter(productor.params.get("outputs") or []), arista_entrada.dataset)
        )
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


__all__ = ["unir_ramas_hermanas", "unir_rechazo_inner_hermano"]
