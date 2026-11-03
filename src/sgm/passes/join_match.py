"""Modelo de coincidencia y tipo de unión de un join que va a un tMap.

Un tMap de Talend resuelve una unión con uno de tres modelos de coincidencia:
- `unique`: devuelve la última fila coincidente de la búsqueda (documentado en
  https://help.qlik.com/talend/en-US/components/8.0/tmap/example-job-implementing-different-match-models);
- `first`: devuelve la primera fila coincidente;
- `all`: devuelve todas las filas coincidentes.

El tMap solo admite las uniones inner y left outer. Este módulo deja el modelo y el tipo escritos
en el componente, con sus advertencias, para que ninguno quede implícito.

Un SQL con `join ... on` devuelve todas las parejas que cumplen la condición: su modelo es `all`
sin advertencia. Un MERGE no dice cuántas filas repiten la clave en cada lado, así que se marca
`all` como suposición con advertencia. Ninguna construcción SAS actual demuestra `unique` ni
`first`: ese valor se acepta aquí, pero solo se emite si una fuente lo demuestra.
"""

from __future__ import annotations

from typing import Any

from sgm.ir.models import Operator

MATCH_MODELS = ("unique", "first", "all")
#: Tipos de unión que el tMap admite, con el nombre que usa en su interfaz.
TMAP_JOIN_TYPES = {"inner": "inner", "left": "left outer"}

_UNIQUE_NOTE = (
    "unique match: el tMap conserva la última fila coincidente de la búsqueda, no la primera. "
    "Si SAS toma otra fila para la misma clave, el resultado difiere; revisar antes de migrar."
)
_FIRST_NOTE = (
    "first match: el tMap conserva la primera fila coincidente de la búsqueda; confirmar que el "
    "orden de la búsqueda coincide con el de SAS."
)
_MERGE_NOTE = (
    "MERGE: el modelo 'all' es una suposición. SAS empareja filas en secuencia cuando la clave se "
    "repite en ambos lados; revisar la cardinalidad antes de migrar."
)


def _model_note(model: str, op: Operator) -> str | None:
    if model == "unique":
        return _UNIQUE_NOTE
    if model == "first":
        return _FIRST_NOTE
    if op.params.get("keys") is None:  # MERGE: no tiene `keys`, solo `by`
        return _MERGE_NOTE
    return None


def describe(op: Operator, model: str | None = None) -> dict[str, Any]:
    """Modelo de coincidencia, tipo de unión del tMap y advertencias de un join.

    `model` solo lo fija quien ya tenga una fuente que lo demuestra; por omisión se usa el
    modelo por defecto del tipo de construcción.
    """
    if model is not None and model not in MATCH_MODELS:
        raise ValueError(f"modelo de coincidencia desconocido: {model}")
    chosen = model or "all"
    kind = op.params.get("join_type")
    tmap_type = TMAP_JOIN_TYPES.get(kind)
    notes: list[str] = []
    note = _model_note(chosen, op)
    if note:
        notes.append(note)
    if tmap_type is None:
        notes.append(
            f"tipo de unión {kind or 'no deducido'}: el tMap solo admite inner o left outer; "
            "revisar antes de migrar."
        )
    return {"match_model": chosen, "join_type": tmap_type, "notes": notes}


def attach(op: Operator, component: dict[str, Any]) -> None:
    """Escribe el modelo y el tipo en el componente tMap y deja las advertencias en el operador.

    Las advertencias se añaden una sola vez (no se repiten si el paso se ejecuta de nuevo).
    """
    info = describe(op)
    component["match_model"] = info["match_model"]
    component["join_type"] = info["join_type"]
    for text in info["notes"]:
        if text not in op.notes:
            op.notes.append(text)


def attach_map(op: Operator, component: dict[str, Any]) -> None:
    """Joins fundidos en un `map` (pasada 6): cada paso de join recibe su modelo y su tipo.

    El componente `tMap` lleva la lista `joins`; las advertencias van al operador una sola vez.
    """
    component["joins"] = []
    for step in op.params.get("steps", []):
        if step.get("kind") != "join":
            continue
        paso = Operator(id=op.id, kind="join", params=dict(step.get("params", {})))
        info = describe(paso)
        component["joins"].append(
            {
                "firma": step.get("signature", ""),
                "match_model": info["match_model"],
                "join_type": info["join_type"],
            }
        )
        for text in info["notes"]:
            if text not in op.notes:
                op.notes.append(text)
