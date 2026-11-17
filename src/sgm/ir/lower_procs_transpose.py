"""PROC TRANSPOSE: el pivote queda como hueco explícito hasta que un caso lo pida (B-8).

El constructor `pivotar` (ir/operadores.py) existe, pero no hay un componente Talend que lo emita ni
una regla demostrada de SAS para todas sus opciones. Por eso el operador sale `hueco` con su motivo
y la página de la guía (`proc.INDEX.md`, TRANSPOSE Procedure, p. 2745). El emisor lo reporta como
`P-OPERADOR-PIVOTAR`.
"""

from __future__ import annotations

from sgm.ir.builder import Builder
from sgm.ir.models import Evidence

MOTIVO = (
    "PROC TRANSPOSE: el pivote no tiene componente todavía; sus reglas de BY, VAR e ID están en "
    "proc.pdf, TRANSPOSE Procedure, p. 2745, y no hay un caso que las pida"
)


def transpose_hueco(step, ev: Evidence, b: Builder, data: str | None, out: str | None) -> None:
    """Un operador `pivot` en estado `hueco`, con lo que el paso pide y su motivo."""
    statement = "; ".join([step.text, *step.body])
    b.op(
        "pivot",
        {
            "statement": statement,
            "procedure": "transpose",
            "reason": "PROC_NO_SOPORTADO",  # el motivo que usan el informe de huecos y `explain`
            "data": data,
            "out": out,
            "by": step.clauses.get("by"),
            "var": step.clauses.get("var"),
        },
        ev,
        status="hueco",
        notes=[MOTIVO],
    )
