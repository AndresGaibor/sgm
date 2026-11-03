"""Decisiones del usuario por firma y alcance. Gana el alcance más específico.

Orden de búsqueda para un operador: paso (`archivo:línea`), luego archivo, proyecto y global.
Si ninguno existe, queda la opción por defecto de la regla. Las decisiones viven en la base y
tienen la firma como llave:
sobreviven a una recompilación con reglas nuevas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sgm.ir.models import Plan
from sgm.store.db import Store

SCOPES = ("paso", "archivo", "proyecto", "global")


@dataclass(frozen=True)
class Override:
    signature: str
    scope: str
    ref: str
    option: str
    author: str
    reason: str
    date: str


def set_override(
    store: Store,
    signature: str,
    option: str,
    scope: str,
    ref: str = "",
    reason: str = "",
    author: str = "",
) -> Override:
    if scope not in SCOPES:
        raise ValueError(f"alcance desconocido: {scope}; usar uno de {', '.join(SCOPES)}")
    if scope != "global" and not ref:
        raise ValueError(f"el alcance {scope} necesita --ref")
    row = Override(
        signature,
        scope,
        ref if scope != "global" else "",
        option,
        author,
        reason,
        date.today().isoformat(),
    )
    store.conn.execute(
        "INSERT OR REPLACE INTO overrides (signature, scope, ref, option, author, reason, date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (row.signature, row.scope, row.ref, row.option, row.author, row.reason, row.date),
    )
    store.conn.commit()
    return row


def overrides_for(store: Store, signature: str) -> list[Override]:
    rows = store.conn.execute(
        "SELECT * FROM overrides WHERE signature = ?", (signature,)
    ).fetchall()
    return [Override(**{k: r[k] for k in r.keys()}) for r in rows]


def list_overrides(store: Store) -> list[Override]:
    rows = store.conn.execute("SELECT * FROM overrides ORDER BY signature, scope, ref").fetchall()
    return [Override(**{k: r[k] for k in r.keys()}) for r in rows]


def resolve(overrides: list[Override], *, step: str, file: str, project: str) -> Override | None:
    """El override más específico que aplica al paso, al archivo o al proyecto (o global)."""
    by_scope = {o.scope: o for o in overrides}
    for scope, ref in (("paso", step), ("archivo", file), ("proyecto", project), ("global", "")):
        found = by_scope.get(scope)
        if found is not None and (scope == "global" or found.ref == ref):
            return found
    return None


def apply(plan: Plan, store: Store, project: str) -> int:
    """Aplica las decisiones guardadas a los componentes con alternativas. Devuelve cuántas."""
    applied = 0
    for op in plan.graph.operators():
        if not op.component or not op.component.get("alternatives"):
            continue
        found = overrides_for(store, op.signature)
        if not found:
            continue
        ev = op.evidence[0]
        chosen = resolve(found, step=f"{ev.file}:{ev.line_start}", file=ev.file, project=project)
        if chosen is None:
            continue
        options = [op.component["name"], *op.component["alternatives"]]
        if chosen.option not in options:
            continue
        op.component["decision"] = {
            "opcion": chosen.option,
            "alcance": chosen.scope,
            "motivo": chosen.reason,
        }
        op.component["name"] = chosen.option
        applied += 1
    return applied


def joins_sueltos(store: Store, compiled: dict) -> frozenset[str]:
    """Firmas de join fundidos en un tMap que una decisión pide dejar sueltos (`tJoin`).

    Una decisión distinta de `tMap` para ese join exige compilar otra vez con esas firmas fuera de
    la fusión: así la decisión por firma se respeta sin editar el plan a posteriori.
    """
    firmas: set[str] = set()
    for result in compiled.values():
        for op in result.plan.graph.operators():
            if op.kind != "map":
                continue
            for step in op.params.get("steps", []):
                if step.get("kind") != "join":
                    continue
                sig = step.get("signature", "")
                if any(o.option != "tMap" for o in overrides_for(store, sig)):
                    firmas.add(sig)
    return frozenset(firmas)
