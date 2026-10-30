"""Inventario de huecos: por firma, con motivo, archivos, ocurrencias y ejemplo.

Se ordena por número de archivos y, dentro de cada número, por ocurrencias.
Así lo más repetido en más programas aparece primero.
"""

from __future__ import annotations

import json
from collections import defaultdict

from sgm import motivos
from sgm.ir.models import Plan
from sgm.store.db import Store


def inventory(plans: list[Plan]) -> list[dict]:
    """Huecos de todos los planes agrupados por firma."""
    by_signature: dict[str, dict] = {}
    files: dict[str, set[str]] = defaultdict(set)
    occurrences: dict[str, int] = defaultdict(int)
    for plan in plans:
        for gap in plan.gaps:
            entry = by_signature.setdefault(
                gap.signature,
                {"signature": gap.signature, "reason": gap.reason, "example": None},
            )
            for ev in gap.evidence:
                files[gap.signature].add(ev.file)
                occurrences[gap.signature] += 1
                if entry["example"] is None:
                    entry["example"] = {
                        "texto": gap.text,
                        "file": ev.file,
                        "line_start": ev.line_start,
                        "line_end": ev.line_end,
                    }
    rows = []
    for signature, entry in by_signature.items():
        rows.append(
            {
                **entry,
                "files": sorted(files[signature]),
                "occurrences": occurrences[signature],
            }
        )
    return sorted(rows, key=lambda r: (-len(r["files"]), -r["occurrences"], r["signature"]))


def save(store: Store, rows: list[dict]) -> None:
    """Sustituye el inventario guardado por el de esta compilación."""
    store.conn.execute("DELETE FROM gaps")
    store.conn.executemany(
        "INSERT INTO gaps (signature, reason, files, occurrences, example) VALUES (?, ?, ?, ?, ?)",
        [
            (
                r["signature"],
                r["reason"],
                json.dumps(r["files"]),
                r["occurrences"],
                json.dumps(r["example"]),
            )
            for r in rows
        ],
    )
    store.conn.commit()


def _fila(item: dict) -> dict:
    """Une un hueco con su dueño, su arreglo y el comando que lo empieza (`routing.yaml`)."""
    motivo = motivos.de(item["reason"])
    tipo = motivo.tipo_regla if motivo else None
    if tipo:
        comando = f"sgm rules new {tipo} --from-gap {item['signature']}"
    else:
        comando = f"sgm case new --from-gap {item['signature']}"
    return {
        **item,
        "owner": motivo.dueño if motivo else None,
        "fix_with": motivo.se_cierra_con if motivo else "",
        "comando": comando,
    }


def top(store: Store, n: int = 20, owner: str | None = None, file: str | None = None) -> list[dict]:
    """Huecos guardados, ordenados por archivos y ocurrencias.

    `owner` deja solo los de ese dueño; `file` solo los que aparecen en un archivo que contenga ese
    texto. `n` limita el resultado.
    """
    rows = store.conn.execute("SELECT * FROM gaps").fetchall()
    items = [
        _fila(
            {
                "signature": r["signature"],
                "reason": r["reason"],
                "files": json.loads(r["files"]),
                "occurrences": r["occurrences"],
                "example": json.loads(r["example"]),
            }
        )
        for r in rows
    ]
    if owner:
        items = [i for i in items if i["owner"] == owner]
    if file:
        items = [i for i in items if any(file in f for f in i["files"])]
    items.sort(key=lambda r: (-len(r["files"]), -r["occurrences"], r["signature"]))
    return items[:n]
