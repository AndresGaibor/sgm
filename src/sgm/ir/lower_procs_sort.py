"""Lowering de PROC SORT y su deduplicación posterior."""

from __future__ import annotations

import re

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_procs_common import unsupported
from sgm.ir.models import Evidence, Operator


def lower_sort(step: Proc, evidence: Evidence, builder: Builder) -> None:
    data = step.options.get("data")
    out = step.options.get("out")
    by, descending, error = _sort_keys(step.clauses.get("by"))
    flags = set(step.flags)
    nodupkey = "nodupkey" in flags
    noduprec = bool(flags & {"nodup", "noduprec", "noduprecs"})
    dupout = step.options.get("dupout")
    opciones_desconocidas = sorted(set(step.options) - {"data", "out", "dupout"})
    banderas_admitidas = {"nodupkey", "nodup", "noduprec", "noduprecs", "equals", "noequals"}
    banderas_desconocidas = sorted(flags - banderas_admitidas)
    sentencias_desconocidas = [
        sentencia
        for sentencia in step.body
        if sentencia and sentencia.split(None, 1)[0].lower() != "by"
    ]
    if error:
        unsupported(step, evidence, builder, error)
        return
    if opciones_desconocidas or banderas_desconocidas or sentencias_desconocidas:
        desconocidos = sorted(
            [*opciones_desconocidas, *banderas_desconocidas]
            + [sentencia.split(None, 1)[0].lower() for sentencia in sentencias_desconocidas]
        )
        detalle = ", ".join(desconocidos)
        nota = f"PROC SORT contiene opciones o sentencias aún no traducidas: {detalle}"
        unsupported(step, evidence, builder, nota)
        return
    if {"equals", "noequals"} <= flags:
        unsupported(step, evidence, builder, "PROC SORT combina EQUALS y NOEQUALS")
        return
    if nodupkey and noduprec:
        unsupported(
            step,
            evidence,
            builder,
            "PROC SORT combina NODUPKEY con NODUPREC; la combinación no está verificada",
        )
        return
    if dupout and not nodupkey:
        unsupported(step, evidence, builder, "DUPOUT= solo se admite junto con NODUPKEY")
        return
    salidas = [qualify(nombre).lower() for nombre in (dupout, out) if nombre]
    dupout_reemplaza_entrada = bool(
        dupout and data and qualify(dupout).lower() == qualify(data).lower()
    )
    if len(salidas) != len(set(salidas)) or dupout_reemplaza_entrada:
        unsupported(step, evidence, builder, "DUPOUT= no puede compartir dataset con DATA= u OUT=")
        return
    es_by_all = by == ["_all_"]
    if noduprec and not es_by_all:
        notes = [
            "NODUPREC solo elimina duplicados adyacentes; sin BY _ALL_ no se demuestra "
            "que todos queden juntos"
        ]
        builder.op(
            "sort",
            {
                **_sort_params(by, descending, flags, data),
                "outputs": [qualify(out or data)] if (out or data) else [],
            },
            evidence,
            status="parcial",
            notes=notes,
        )
        return
    nodup = nodupkey or noduprec
    sort_status = "soportado" if by else "parcial"
    sort_notes = [] if by else ["PROC SORT sin BY: no se puede deducir la clave"]
    sort = builder.op(
        "sort",
        _sort_params(by, descending, flags, data),
        evidence,
        status=sort_status,
        notes=sort_notes,
    )
    current: Operator = sort
    if nodup:
        notes = [] if by else ["NODUPKEY sin clave: deduplicación parcial"]
        dedup_status = "soportado" if by else "parcial"
        if nodupkey and by:
            dedup_status = "parcial"
            notes.append(
                "EQUALS conserva empates en orden de entrada; la estabilidad de tSortRow "
                "no está verificada para identificar la misma fila"
            )
        if nodupkey and "noequals" in flags:
            dedup_status = "parcial"
            notes.append("NOEQUALS permite cambiar qué observación queda por cada clave duplicada")
        params = {"by": by, "keep": "first"}
        if dupout:
            params["duplicate_outputs"] = [qualify(dupout)]
        dedup = builder.op("dedup", params, evidence, status=dedup_status, notes=notes)
        builder.link(sort, dedup)
        current = dedup
    target = out or data
    if target:
        current.params["outputs"] = [qualify(target)]
        builder.refresh(current)


def _sort_params(
    by: list[str], descending: list[bool], flags: set[str], data: str | None
) -> dict[str, object]:
    """Guarda solo opciones no predeterminadas para mantener estables las firmas del plan."""
    params: dict[str, object] = {"by": by, "inputs": [qualify(data)] if data else []}
    if any(descending):
        params["descending"] = descending
    if "noequals" in flags:
        params["equals"] = False
    return params


def _sort_keys(clause: str | None) -> tuple[list[str], list[bool], str | None]:
    """Lee BY y aplica DESCENDING solo a la variable que le sigue, como en SAS."""
    if not clause:
        return [], [], None
    match = re.match(r"(?is)^\s*by\b(.*?);?\s*$", clause)
    if not match:
        return [], [], "PROC SORT recibió una cláusula BY que no se pudo interpretar"
    tokens = match.group(1).split()
    names: list[str] = []
    descending: list[bool] = []
    pending_descending = False
    for token in tokens:
        clean = token.rstrip(";")
        if clean.lower() == "descending":
            if pending_descending:
                return [], [], "PROC SORT contiene DESCENDING sin variable asociada"
            pending_descending = True
            continue
        if not re.fullmatch(r"(?i)[a-z_][a-z0-9_]*", clean):
            return [], [], f"PROC SORT BY contiene un nombre no admitido: {clean}"
        if pending_descending and clean.lower() == "_all_":
            return [], [], "DESCENDING _ALL_ no está verificado para PROC SORT"
        names.append(clean.lower())
        descending.append(pending_descending)
        pending_descending = False
    if pending_descending:
        return [], [], "PROC SORT contiene DESCENDING sin variable asociada"
    return names, descending, None
