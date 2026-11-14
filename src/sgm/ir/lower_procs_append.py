"""Lowering de PROC APPEND con salida sobre BASE y creación explícita en WORK."""

from __future__ import annotations

from typing import Any

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_procs_common import unsupported
from sgm.ir.models import Evidence
from sgm.ir.proc_rules import lower_declared

P_APPEND_BASE_EXTERNA = "P-APPEND-BASE-EXTERNA-SIN-FUENTE"


def _ya_producida(dataset: str, builder: Builder) -> bool:
    """Indica si una operación anterior del programa escribe la tabla."""
    objetivo = dataset.casefold()
    for operator in builder.created:
        nombres = [
            *(operator.params.get("outputs") or []),
            *(operator.params.get("duplicate_outputs") or []),
        ]
        if any(str(nombre).casefold() == objetivo for nombre in nombres):
            return True
    return False


def lower_append(
    step: Proc, evidence: Evidence, builder: Builder, spec: dict[str, Any]
) -> bool:
    """Emite unión acumulativa o copia de DATA cuando BASE nueva es de WORK.

    La existencia se decide contra las escrituras previas de este programa. Las versiones del
    grafo se asignan después, en p01_graph, para que todos los escritores usen el mismo mecanismo.
    """
    base = step.options.get("base")
    data = step.options.get("data")
    if not base or not data:
        return False

    dataset_base = qualify(str(base))
    dataset_data = qualify(str(data))
    if _ya_producida(dataset_base, builder):
        if not lower_declared(spec, step, evidence, builder, data, None):
            return False
        operator = builder.created[-1]
    elif dataset_base.upper().startswith("WORK."):
        operator = builder.op(
            "map",
            {"inputs": [dataset_data], "outputs": [dataset_base], "steps": []},
            evidence,
            notes=["PROC APPEND crea BASE nueva en WORK con las filas de DATA"],
        )
    else:
        unsupported(
            step,
            evidence,
            builder,
            "Pendiente: P-APPEND-BASE-EXTERNA-SIN-FUENTE; no se demuestra si la tabla "
            "permanente existe ni cómo se lee y actualiza en el destino; proc.pdf, p. 639",
            pending_code=P_APPEND_BASE_EXTERNA,
        )
        return True

    operator.origin = "proc_append"
    return True


__all__ = ["P_APPEND_BASE_EXTERNA", "lower_append"]
