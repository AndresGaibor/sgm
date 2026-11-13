"""`UPDATE` y `MODIFY` del DATA step (B-19; lrcon pp. 602 a 611; lestmtsref pp. 362 y 252).

`UPDATE` queda como un `join` con `modo="update"` y estado `hueco`: el intérprete lo calcula
(`interprete_update.py`), pero no hay emisor en Talend todavía, así que el Job no se escribe
(decisión 5). Con `UPDATEMODE=` el pendiente es `P-UPDATEMODE`. `MODIFY` modifica el dataset en el
sitio, sin equivalente en un Job que lee y escribe tablas: hueco `P-MODIFY-EN-SITIO`.
"""

from __future__ import annotations

import re

from sgm.ir.models import Evidence, Operator


def lower_actualizacion(
    stmts: list, fuentes: list[str], entradas: list[Operator], ev: Evidence, b
) -> Operator:
    """Operador de `UPDATE` o `MODIFY` enlazado a sus entradas; `fuentes`: datasets calificados."""
    sentencia = next(s for s in stmts if s.kind in ("update", "modify"))
    if sentencia.kind == "modify":
        op = b.op(
            "unsupported",
            {"codigo": "P-MODIFY-EN-SITIO", "reason": "modify"},
            ev,
            status="hueco",
            notes=[
                "MODIFY modifica el dataset en el sitio; el Job no sobrescribe su propia entrada "
                "(lestmtsref, p. 252; lrcon, p. 605)"
            ],
        )
    else:
        by = next((s.fields["names"] for s in stmts if s.kind == "by"), [])
        con_modo = bool(re.search(r"(?i)\bupdatemode\s*=", sentencia.text))
        codigo = "P-UPDATEMODE" if con_modo else "P-UPDATE-SIN-EMISOR"
        op = b.op(
            "join",
            {
                "modo": "update",
                "by": [n.lower() for n in by],
                "sources": fuentes,
                "updatemode": con_modo,
                "codigo": codigo,
            },
            ev,
            status="hueco",
            notes=[
                "UPDATE sin emisor en Talend todavía (lrcon, pp. 604 a 605; B-19)"
                if not con_modo
                else "UPDATEMODE=NOMISSINGCHECK no tiene caso todavía (lrcon, p. 610)"
            ],
        )
    for entrada in entradas:
        b.link(entrada, op)
    return op
