"""Inventario de huecos: por firma, con motivo, archivos, ocurrencias y ejemplo.

Se ordena por número de archivos y, dentro de cada número, por ocurrencias.
Así lo más repetido en más programas aparece primero.
"""

from __future__ import annotations

import json
from collections import defaultdict

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


def top(store: Store, n: int = 20) -> list[dict]:
    rows = store.conn.execute("SELECT * FROM gaps").fetchall()
    items = [
        {
            "signature": r["signature"],
            "reason": r["reason"],
            "files": json.loads(r["files"]),
            "occurrences": r["occurrences"],
            "example": json.loads(r["example"]),
        }
        for r in rows
    ]
    items.sort(key=lambda r: (-len(r["files"]), -r["occurrences"], r["signature"]))
    return items[:n]
