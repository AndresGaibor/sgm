"""Pasada 2: fontanería de SAS que no se migra (sesión, esperas, temporales, mensajes, medición).

La clasificación es por forma: los patrones están en `plumbing_patterns.py` y se aplican al texto de
cada operador. Además, `proc delete` y `proc datasets` que borran solo la biblioteca WORK son
fontanería; si borran una biblioteca permanente no lo son.

Las dos fases existen porque p03 necesita ver los comandos de shell y las esperas para reconocer una
carga externa. Por eso `mark` solo marca y registra en `plan.not_migrated`. `remove_marked` quita
del grafo los operadores marcados que sobrevivan a p03; lo llama p03 al final.
"""

from __future__ import annotations

import re

from sgm.ir.models import Graph, NotMigrated, Operator
from sgm.ir.signature import signature
from sgm.passes.base import PassContext, PassLog
from sgm.passes.plumbing_patterns import match_plumbing
from sgm.sas_scope import is_work_dataset, is_work_delete, is_work_library

NAME = "p02_plumbing"
_WORK_CLEANUP = re.compile(r"(?is)^\s*proc\s+(delete|datasets)\b")
_LIBRARY = re.compile(r"(?i)\blib(?:rary)?\s*=\s*(\S+)")


def primary_text(op: Operator) -> str:
    """Sentencia principal del operador (la que se clasifica al empezar la línea)."""
    return str(op.params.get("statement") or op.params.get("sql") or op.params.get("text") or "")


def op_text(op: Operator) -> str:
    """Texto completo del operador: sentencia principal más sentencias no traducidas y asignaciones.
    Texto completo del operador: sentencia principal más sentencias no traducidas y asignaciones."""
    extra = list(op.params.get("untranslated", []))
    extra += [
        f"{a.get('target', '')} = {a.get('expression', '')}"
        for a in op.params.get("assignments", [])
    ]
    return "\n".join([primary_text(op), *extra])


def _work_cleanup(statement: str) -> bool:
    """`proc delete` o `proc datasets` que demuestran tocar exclusivamente WORK."""
    if not _WORK_CLEANUP.match(statement):
        return False
    if re.match(r"(?is)^\s*proc\s+delete\b", statement):
        return is_work_delete(statement)
    if not re.search(r"(?i)\b(delete|kill)\b", statement):
        return False
    library = _LIBRARY.search(statement)
    return bool(library and is_work_library(library.group(1)))


def classify(op: Operator, report_policy: str = "discard") -> tuple[str, str, str] | None:
    """(categoría, qué hace, equivalente en Talend) si el operador es fontanería; None si no."""
    if op.status == "reemplazado" and op.params.get("reason") == "CONFIGURACION":
        return None
    if _work_cleanup(primary_text(op)):
        return (
            "limpieza_work",
            "borrado de datasets temporales de WORK (PROC DELETE o PROC DATASETS)",
            "La salida y las tablas temporales no existen en Talend: el flujo no las necesita.",
        )
    found = match_plumbing(primary_text(op)) or match_plumbing(op_text(op))
    if found is None:
        return None
    if found.category == "ods_close" and report_policy != "discard":
        return None
    return found.category, found.what, found.talend


def _report(op: Operator, ctx: PassContext) -> bool:
    """Reporte impreso según `reports`; solo PRINT tiene salida de filas equivalente.

    `discard`: no se migra (queda en no migrados). `log`: un `report` que va a `tLogRow`.
    `csv`: un `write_file` a un fichero cuya ruta es un contexto del Job. Para otros PROCs,
    el contenido tabular no está demostrado y se conserva el hueco.
    """
    reason = op.params.get("reason")
    if reason == "LIMPIEZA":
        op.status = "reemplazado"
        op.params["plumbing"] = "limpieza_work"
        notice = next(
            (note for note in op.notes if "A-PROC-LIMPIEZA-OMITIDO" in note),
            "A-PROC-LIMPIEZA-OMITIDO: limpieza de un temporal de WORK",
        )
        ctx.plan.not_migrated.append(
            NotMigrated(
                op.id,
                notice,
                "No aplica: las tablas temporales de WORK no se materializan en Talend.",
                list(op.evidence),
            )
        )
        return True
    if reason != "REPORTE":
        return False
    policy = ctx.project.reports
    procedure = str(op.params.get("procedure", "")).upper()
    if policy != "discard" and procedure != "PRINT":
        return False
    inputs = list(op.params.get("inputs", []))
    if policy == "discard":
        op.status = "reemplazado"
        contents_work = procedure == "CONTENTS" and any(
            is_work_dataset(dataset, default_work=False) for dataset in inputs
        )
        if contents_work:
            op.params["plumbing"] = "limpieza_work"
            what = (
                "A-PROC-LIMPIEZA-OMITIDO: salida diagnóstica de PROC CONTENTS descartada; "
                "alcance WORK demostrado"
            )
            talend = "No aplica: reports=discard omite la salida diagnóstica del miembro de WORK."
        else:
            op.params["plumbing"] = "reporte_diagnostico"
            what = f"PROC {procedure} de diagnóstico: reporte impreso"
            talend = "No se migra: reporte de diagnóstico (reports = discard)"
        ctx.plan.not_migrated.append(
            NotMigrated(
                op.id,
                what,
                talend,
                list(op.evidence),
            )
        )
    elif policy == "log":
        op.kind = "report"
        op.status = "soportado"
        op.params = {"procedure": procedure.lower(), "inputs": inputs}
    else:
        op.kind = "write_file"
        op.status = "soportado"
        op.params = {
            "inputs": inputs,
            "outfile": f"contexto.ruta_{procedure.lower()}",
            "dbms": "csv",
        }
    op.signature = signature(op.kind, op.params)
    return True


def mark(graph: Graph, ctx: PassContext) -> PassLog:
    """Marca los operadores de fontanería y los registra con su equivalente. No los quita todavía.
    Los reportes impresos los decide la política `reports` (ver `_report`)."""
    log = PassLog(NAME)
    for op in graph.operators():
        if _report(op, ctx):
            metric = "omisiones_work" if op.params.get("reason") == "LIMPIEZA" else "reportes"
            log.metrics[metric] = log.metrics.get(metric, 0) + 1
            continue
        found = classify(op, ctx.project.reports)
        if found is None:
            continue
        category, what, talend = found
        op.status = "reemplazado"
        op.params["plumbing"] = category
        ctx.plan.not_migrated.append(NotMigrated(op.id, what, talend, list(op.evidence)))
        log.metrics[category] = log.metrics.get(category, 0) + 1
    log.notes.append(f"{sum(log.metrics.values())} operadores de fontanería marcados")
    return log


def remove_marked(graph: Graph, ctx: PassContext) -> PassLog:
    """Quita del grafo los operadores marcados que siguen ahí, reconectando sus entradas y salidas.
    Quita del grafo los operadores marcados que siguen ahí, reconectando sus entradas y salidas."""
    log = PassLog(NAME + ".quitar")
    for op in graph.operators():
        if "plumbing" not in op.params:
            continue
        graph.bypass(op.id)
        log.removed.append({"op": op.id, "motivo": str(op.params["plumbing"])})
    log.metrics["quitados"] = len(log.removed)
    return log
