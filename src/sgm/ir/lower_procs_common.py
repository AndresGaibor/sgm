"""Helpers compartidos por los lowerings de procedimientos."""

from __future__ import annotations

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder
from sgm.ir.models import Evidence


def unsupported(
    step: Proc, evidence: Evidence, builder: Builder, note: str, *,
    pending_code: str | None = None, inputs: list[str] | None = None,
) -> None:
    """Registra un PROC no traducido, conservando su texto y su código si existe."""
    statement = "; ".join([step.text, *step.body])
    params = {"statement": statement, "procedure": step.name, "reason": "PROC_NO_SOPORTADO"}
    if pending_code:
        params["pending_code"] = pending_code
    if inputs is not None:
        params["inputs"] = inputs
    builder.op("unsupported", params, evidence, status="hueco", notes=[note])
