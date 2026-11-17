"""Sumideros muertos: asignaciones que no llegan a ninguna salida (B-17).

Un `derive` sin sucesores y sin `outputs` no alimenta ningún dataset. Pasa tras el último `OUTPUT`
de un paso: el PDV ya se escribió (`lrcon`, p. 498) y la asignación no entra en lo escrito.
Se quita solo si el paso tiene alguna escritura; si no, se deja como estaba.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sgm.ir.models import Plan

if TYPE_CHECKING:
    from sgm.optimizar import Informe


def quitar_sumideros_muertos(plan: Plan, informe: "Informe") -> bool:
    """Quita los `derive` sin salida y anota la decisión. True si quitó alguno."""
    from sgm.optimizar import Decision  # import tardío: `optimizar` importa este módulo

    if not any(op.kind in ("write", "write_file") for op in plan.graph.operators()):
        return False
    muertos = [
        op
        for op in plan.graph.operators()
        if op.kind == "derive"
        and not op.params.get("outputs")
        and not plan.graph.successors(op.id)
    ]
    for op in muertos:
        # El operador quitado lo representa su predecesor, como en las fusiones de `optimizar`.
        predecesores = plan.graph.predecessors(op.id)
        informe.absorbidos[op.id] = predecesores[0] if predecesores else op.id
        lineas = tuple(sorted({ev.line_start for ev in op.evidence}))
        informe.decisiones.append(
            Decision(
                "sumidero_muerto",
                "asignación después del último OUTPUT: no llega a ningún dataset",
                lineas,
            )
        )
        plan.graph.remove_operator(op.id)
        _quitar_de_trabajos(plan, op.id)
    return bool(muertos)


def _quitar_de_trabajos(plan: Plan, op_id: str) -> None:
    """El Job que lo listaba ya no debe nombrar al operador quitado (ni sus subjobs hijos)."""
    pendientes = list(plan.jobs)
    while pendientes:
        job = pendientes.pop()
        job.subjobs = [[i for i in sub if i != op_id] for sub in job.subjobs]
        pendientes.extend(job.children)
