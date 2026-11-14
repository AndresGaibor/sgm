"""Resolución estática de conexiones declaradas por los consumidores de SQL de base."""

from __future__ import annotations

from dataclasses import dataclass

from sgm.ir.models import Operator, Plan
from sgm.talend_item.desde_plan_conexion import variables_de_motor


@dataclass(frozen=True)
class Conexion:
    """Una conexión lógica de SAS identificada por su alias y motor."""

    alias: str
    motor: str
    variables: tuple[str, ...]
    opciones: str = ""
    linea: int | None = None


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def conexiones_de_plan(plan: Plan) -> list[Conexion]:
    """Deduplica por alias/motor las conexiones usadas por SELECT y EXECUTE pass-through."""
    conexiones: dict[tuple[str, str], Conexion] = {}
    for op in plan.graph.operators():
        if op.kind not in {"read", "exec_sql"} or not (op.placement or "").startswith("db:"):
            continue
        motor = str(op.params.get("engine") or op.placement.removeprefix("db:")).casefold()
        alias = str(op.params.get("connection_alias") or motor)
        opciones = str(op.params.get("connection_options") or "")
        try:
            variables = variables_de_motor(motor)
        except ValueError:
            variables = ()
        clave = (alias.casefold(), motor)
        actual = conexiones.get(clave)
        if actual is None:
            conexiones[clave] = Conexion(alias, motor, variables, opciones, _linea(op))
        elif not actual.opciones and opciones:
            conexiones[clave] = Conexion(alias, motor, variables, opciones, actual.linea)
    return list(conexiones.values())


__all__ = ["Conexion", "conexiones_de_plan", "variables_de_motor"]
