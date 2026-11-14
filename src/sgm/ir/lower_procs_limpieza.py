"""Lowering acotado para limpiezas de WORK y copias de bibliotecas SAS."""

from __future__ import annotations

import re

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_procs_common import unsupported
from sgm.ir.models import Evidence
from sgm.sas_scope import (
    explicit_dataset_libraries,
    is_work_delete,
    is_work_library,
)

P_DELETE_PERSISTENTE = "P-DELETE-PERSISTENTE"
P_DELETE_BIBLIOTECA_SIN_DEMOSTRAR = "P-DELETE-BIBLIOTECA-SIN-DEMOSTRAR"
P_COPY_SIN_LISTA = "P-COPY-SIN-LISTA"
P_COPY_PERSISTENTE = "P-COPY-PERSISTENTE"
P_COPY_MISMA_BIBLIOTECA = "P-COPY-MISMA-BIBLIOTECA"
P_COPY_OPCION_NO_SOPORTADA = "P-COPY-OPCION-NO-SOPORTADA"

_LIBREF = re.compile(r"(?i)^[a-z_][a-z0-9_]*$")
_SELECT = re.compile(r"(?is)^\s*select\b(.*?);?\s*$")
_DELETE = re.compile(r"(?i)^\s*delete\b\s*.+;?\s*$")


def _statement(step: Proc) -> str:
    return "; ".join([step.text, *step.body])


def _literal_libref(value: str | None) -> str | None:
    """Normaliza un libref literal sin resolver macros ni valores de ejecución."""
    if not value:
        return None
    name = value.strip().strip("'\"")
    return name if _LIBREF.fullmatch(name) else None


def _cleanup(step: Proc, evidence: Evidence, builder: Builder, detail: str) -> None:
    note = f"A-PROC-LIMPIEZA-OMITIDO: {detail}; alcance WORK demostrado"
    builder.op(
        "unsupported",
        {"statement": _statement(step), "procedure": step.name, "reason": "LIMPIEZA"},
        evidence,
        status="hueco",
        notes=[note],
    )


def _pending(
    step: Proc,
    evidence: Evidence,
    builder: Builder,
    code: str,
    detail: str,
    source: str,
) -> None:
    unsupported(
        step,
        evidence,
        builder,
        f"Pendiente: {code}; {detail}; se documenta en {source}",
        pending_code=code,
    )


def _delete(step: Proc, evidence: Evidence, builder: Builder) -> None:
    library = step.options.get("library") or step.options.get("lib")
    literal_library = _literal_libref(library)
    if not step.options.get("data"):
        unsupported(step, evidence, builder, "PROC DELETE requiere DATA= (proc.pdf, p. 839)")
    elif is_work_delete(_statement(step)):
        _cleanup(step, evidence, builder, "PROC DELETE")
    elif library and literal_library and not is_work_library(literal_library):
        _pending(
            step,
            evidence,
            builder,
            P_DELETE_PERSISTENTE,
            "LIBRARY= nombra explícitamente una biblioteca distinta de WORK",
            "proc.pdf, pp. 839, 847",
        )
    elif any(
        not is_work_library(library)
        for library in explicit_dataset_libraries(step.options.get("data"))
    ):
        _pending(
            step,
            evidence,
            builder,
            P_DELETE_PERSISTENTE,
            "DATA= nombra explícitamente una biblioteca distinta de WORK",
            "proc.pdf, pp. 839, 847",
        )
    else:
        _pending(
            step,
            evidence,
            builder,
            P_DELETE_BIBLIOTECA_SIN_DEMOSTRAR,
            "DATA= no demuestra si todos los miembros borrados pertenecen a WORK",
            "proc.pdf, pp. 839, 847",
        )


def _datasets(step: Proc, evidence: Evidence, builder: Builder) -> None:
    library = step.options.get("library") or step.options.get("lib")
    deletes = [line for line in step.body if _DELETE.match(line)]
    only_deletes = len(deletes) == len([line for line in step.body if line.strip()])
    kills_all = "kill" in step.flags and not step.body
    opciones_desconocidas = set(step.options) - {"library", "lib"}
    banderas_desconocidas = set(step.flags) - {"nolist", "kill"}
    literal_library = _literal_libref(library)
    if not library:
        _pending(
            step,
            evidence,
            builder,
            P_DELETE_BIBLIOTECA_SIN_DEMOSTRAR,
            "la biblioteca de PROC DATASETS no está demostrada como WORK",
            "proc.pdf, pp. 616, 627",
        )
    elif literal_library is None:
        _pending(
            step,
            evidence,
            builder,
            P_DELETE_BIBLIOTECA_SIN_DEMOSTRAR,
            "LIBRARY= de PROC DATASETS no es un libref literal",
            "proc.pdf, pp. 616, 627",
        )
    elif not is_work_library(literal_library):
        _pending(
            step,
            evidence,
            builder,
            P_DELETE_PERSISTENTE,
            "LIBRARY= nombra explícitamente una biblioteca distinta de WORK",
            "proc.pdf, pp. 616, 627",
        )
    elif (
        (only_deletes and deletes or kills_all)
        and not opciones_desconocidas
        and not banderas_desconocidas
    ):
        _cleanup(step, evidence, builder, "PROC DATASETS DELETE")
    else:
        unsupported(
            step,
            evidence,
            builder,
            "PROC DATASETS contiene acciones u opciones fuera de la limpieza DELETE de WORK "
            "(proc.pdf, p. 627)",
        )


def _selected_members(step: Proc) -> list[str] | None:
    selects = [match for line in step.body if (match := _SELECT.fullmatch(line))]
    if len(selects) != 1:
        return None
    names = selects[0].group(1).replace(",", " ").split()
    if not names or any(not _LIBREF.fullmatch(name) for name in names):
        return None
    if len({name.casefold() for name in names}) != len(names):
        return None
    if any(not _SELECT.match(line) for line in step.body if line.strip()):
        return None
    return names


def _copy(step: Proc, evidence: Evidence, builder: Builder) -> None:
    selected = _selected_members(step)
    if selected is None:
        _pending(
            step,
            evidence,
            builder,
            P_COPY_SIN_LISTA,
            "PROC COPY no contiene una lista SELECT estática de miembros",
            "proc.pdf, pp. 573–575",
        )
        return
    input_library = step.options.get("in")
    output_library = step.options.get("out")
    if (
        not input_library
        or not output_library
        or not _LIBREF.fullmatch(input_library)
        or not _LIBREF.fullmatch(output_library)
    ):
        unsupported(
            step,
            evidence,
            builder,
            "PROC COPY requiere IN= y OUT= estáticos (proc.pdf, pp. 573–575)",
        )
        return
    opciones_desconocidas = set(step.options) - {"in", "out"}
    if opciones_desconocidas or step.flags:
        _pending(
            step,
            evidence,
            builder,
            P_COPY_OPCION_NO_SOPORTADA,
            "PROC COPY contiene opciones o banderas no modeladas",
            "proc.pdf, p. 575",
        )
        return
    if input_library.casefold() == output_library.casefold():
        _pending(
            step,
            evidence,
            builder,
            P_COPY_MISMA_BIBLIOTECA,
            "IN= y OUT= nombran la misma biblioteca; el efecto de copiar miembros sobre sí mismos "
            "no está modelado",
            "proc.pdf, pp. 573–575",
        )
        return
    if not is_work_library(output_library):
        _pending(
            step,
            evidence,
            builder,
            P_COPY_PERSISTENTE,
            "OUT= apunta a una biblioteca persistente y copiaría datos fuera del Job",
            "proc.pdf, p. 575",
        )
        return
    for name in selected:
        source = qualify(f"{input_library}.{name}")
        destination = qualify(f"{output_library}.{name}")
        reader = builder.op("read", {"dataset": source}, evidence)
        writer = builder.op("write", {"dataset": destination}, evidence)
        builder.link(reader, writer, dataset=source)


def lower_limpieza(step: Proc, evidence: Evidence, builder: Builder) -> bool:
    """Baja solo formas demostradas; False deja al llamador aplicar el fallback general."""
    if step.name == "delete":
        _delete(step, evidence, builder)
    elif step.name == "datasets":
        _datasets(step, evidence, builder)
    elif step.name == "copy":
        _copy(step, evidence, builder)
    else:
        return False
    return True
