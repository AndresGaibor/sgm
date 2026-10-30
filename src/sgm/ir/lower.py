"""Pasos sintácticos a operadores lógicos. Todo operador lleva la evidencia de su paso."""

from __future__ import annotations

from collections.abc import Iterable

from sgm.frontend.datastep import DataStep
from sgm.frontend.macros import MacroDynamic
from sgm.frontend.steps import (
    Global,
    Include,
    Let,
    Libname,
    MacroCall,
    Options,
    Proc,
    ProcSql,
    Unparsed,
    XCommand,
)
from sgm.ir.builder import Builder
from sgm.ir.lower_data import lower_data
from sgm.ir.lower_procs import lower_proc
from sgm.ir.lower_sql import lower_proc_sql
from sgm.ir.models import Evidence, Graph


def _evidence(item) -> Evidence:
    step = item.item
    start = getattr(step, "line", item.line)
    end = getattr(step, "end_line", start)
    return Evidence(file=item.file, line_start=start, line_end=end, label=item.label)


def _config(step, ev: Evidence, b: Builder, what: str) -> None:
    """Configuración de sesión o de macro: la resuelve el contexto del Job."""
    b.op(
        "unsupported",
        {"statement": what, "reason": "CONFIGURACION"},
        ev,
        status="reemplazado",
        notes=["configuración de sesión o de macro: se resuelve en el contexto del Job"],
    )


def lower_item(item, b: Builder) -> None:
    """Convierte un elemento del programa (paso o dinámico) en operadores."""
    ev = _evidence(item)
    step = item.item
    if isinstance(step, DataStep):
        lower_data(step, ev, b)
    elif isinstance(step, ProcSql):
        lower_proc_sql(step, ev, b)
    elif isinstance(step, Proc):
        lower_proc(step, ev, b)
    elif isinstance(step, MacroDynamic):
        b.op(
            "unsupported",
            {"statement": step.text, "reason": "MACRO_DINAMICA", "detail": step.detail},
            ev,
            status="hueco",
            notes=[step.detail],
        )
    elif isinstance(step, Unparsed):
        b.op(
            "unsupported",
            {"statement": step.text, "reason": "PARSE_ERROR"},
            ev,
            status="hueco",
            notes=[step.reason],
        )
    elif isinstance(step, MacroCall):
        b.op(
            "unsupported",
            {"statement": step.text, "reason": "MACRO_NO_EXPANDIDA"},
            ev,
            status="hueco",
            notes=[f"llamada a %{step.name} que no se pudo expandir"],
        )
    elif isinstance(step, Include):
        b.op(
            "unsupported",
            {"statement": step.text, "reason": "INCLUDE_EXTERNO"},
            ev,
            status="hueco",
            notes=["%INCLUDE fuera del proyecto: el contenido no se conoce"],
        )
    elif isinstance(step, XCommand):
        b.op(
            "unsupported",
            {"statement": step.text, "reason": "COMANDO_SISTEMA"},
            ev,
            status="hueco",
            notes=["comando del sistema operativo"],
        )
    elif isinstance(step, Libname):
        _config(step, ev, b, step.text)
    elif isinstance(step, (Let, Options)):
        _config(step, ev, b, getattr(step, "text", "options"))
    elif isinstance(step, Global):
        b.op(
            "unsupported",
            {"statement": step.text, "reason": "SENTENCIA_NO_SOPORTADA"},
            ev,
            status="hueco",
            notes=["sentencia global sin regla de migración"],
        )


def lower_items(items: Iterable, graph: Graph) -> Builder:
    """Lowering de todo un programa. Devuelve el constructor para seguir numerando operadores."""
    builder = Builder(graph)
    for item in items:
        lower_item(item, builder)
    return builder
