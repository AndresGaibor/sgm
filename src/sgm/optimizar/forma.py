"""Forma de paso fundible: cruces, filtros, asignaciones y modificadores declarativos de salida."""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.ir.models import Operator, Plan

FUSIONABLES = frozenset({"map", "filter", "derive", "join", "select", "rename"})
_PASOS = ("join", "filter", "derive")


class NoFusionable(Exception):
    """La fusión no se puede demostrar; el mensaje dice por qué."""


@dataclass
class Forma:
    """Un operador visto como cruces, filtros y proyección."""

    uniones: list[dict] = field(default_factory=list)
    filtros: list[dict] = field(default_factory=list)
    proyeccion: dict | None = None
    selecciones: list[dict] = field(default_factory=list)
    renombrados: list[dict] = field(default_factory=list)


def nombre_tabla(dataset: object) -> str:
    return str(dataset or "").strip().lower().split(".")[-1]


def forma_de(op: Operator) -> Forma:
    if op.kind not in FUSIONABLES or op.status == "hueco" or op.placement not in (None, "flow"):
        raise NoFusionable(f"el operador '{op.kind}' no se funde")
    if op.params.get("branches"):
        raise NoFusionable("el paso reparte filas en varias salidas")
    pasos = op.params.get("steps") if op.kind == "map" else None
    if pasos is None:
        pasos = [{"kind": op.kind, "params": op.params, "signature": op.signature}]
    forma = Forma()
    orden = 0
    for paso in pasos:
        clase = str(paso.get("kind") or "")
        params = paso.get("params") or {}
        if clase in ("select", "rename"):
            if clase == "select":
                forma.selecciones.append(paso)
            else:
                forma.renombrados.append(paso)
            continue
        if clase not in _PASOS or _PASOS.index(clase) < orden or forma.proyeccion is not None:
            raise NoFusionable(f"el paso '{clase}' no está en la forma cruce, filtro, proyección")
        orden = _PASOS.index(clase)
        if clase == "join":
            if "keys" not in params:
                raise NoFusionable("un MERGE no se funde: empareja fila con fila")
            forma.uniones.append(paso)
        elif clase == "filter":
            forma.filtros.append(paso)
        else:
            if params.get("declared"):
                raise NoFusionable("una declaración de columnas no se funde")
            forma.proyeccion = paso
    return forma


def tabla_derecha(union: dict) -> str | None:
    for par in (union.get("params") or {}).get("keys") or []:
        partes = str(list(par)[1]).split(".") if len(list(par)) == 2 else []
        if len(partes) >= 2:
            return nombre_tabla(partes[-2])
    return None


def entrega(plan: Plan, op_id: str) -> str:
    """Conjunto de datos que entrega un operador, con su biblioteca si la trae."""
    op = plan.graph.operator(op_id)
    if op.kind == "read":
        return str(op.params.get("dataset") or "")
    return str((op.params.get("outputs") or [""])[0])


def parte_de_paso(plan: Plan, op: Operator, forma: Forma) -> str:
    """Conjunto de datos del que parte el paso: el del `FROM`, o su primera entrada."""
    for union in forma.uniones:
        fuentes = (union.get("params") or {}).get("sources") or []
        if fuentes:
            return str(fuentes[0])
    derechas = {tabla_derecha(union) for union in forma.uniones}
    entregas = [entrega(plan, previo) for previo in plan.graph.predecessors(op.id)]
    for dataset in entregas:
        if dataset and nombre_tabla(dataset) not in derechas:
            return dataset
    raise NoFusionable("no se sabe de qué tabla parte el paso")


__all__ = [
    "FUSIONABLES",
    "Forma",
    "NoFusionable",
    "entrega",
    "forma_de",
    "nombre_tabla",
    "parte_de_paso",
    "tabla_derecha",
]
