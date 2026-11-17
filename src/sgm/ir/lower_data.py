"""Pasos DATA a operadores lógicos: lecturas, filtros, derivaciones, uniones y estado por fila."""

from __future__ import annotations

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir import operadores
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_data_grupos import programa_por_grupo
from sgm.ir.lower_data_lectura import _read_file
from sgm.ir.lower_data_lookup import detectar_busqueda
from sgm.ir.lower_data_recorrido import _Recorrido, _statement_evidence
from sgm.ir.lower_data_salidas import (
    _conditional_output,
    _repeated_output_targets,
    _undeclared_output_targets,
)
from sgm.ir.lower_data_union import tipo_de_union
from sgm.ir.lower_data_update import lower_actualizacion
from sgm.ir.models import Evidence, Operator
from sgm.ir.pasos import op_validado
from sgm.ir.types_code import declared_types


def _lower_sources(
    stmts: list[DsStatement], ev: Evidence, b: Builder
) -> tuple[list[Operator], Operator | None]:
    """Lecturas de entrada y la operación que las combina (join, union) si hay más de una."""
    refs: list[dict] = []
    for s in stmts:
        if s.kind in ("set", "merge", "update", "modify"):
            refs += [dict(r, mode=s.kind) for r in s.fields["sources"]]
    reads = [
        b.read_dataset(r["name"], ev, r.get("in") or None, include_in=True) for r in refs
    ]
    entradas: list[Operator] = []
    for ref, read in zip(refs, reads, strict=True):
        where = ref.get("where")
        if where:
            filtrado = op_validado(
                b,
                lambda where=where: operadores.filtrar("_", where, evidence=[ev]),
                "filter",
                {"expression": where},
                ev,
            )
            b.link(read, filtrado)
            entradas.append(filtrado)
        else:
            entradas.append(read)
    if any(s.kind in ("update", "modify") for s in stmts):
        fuentes = [qualify(r["name"]) for r in refs]
        return reads, lower_actualizacion(stmts, fuentes, entradas, ev, b)
    if any(s.kind == "merge" for s in stmts):
        by = next((s.fields["names"] for s in stmts if s.kind == "by"), [])
        join_type = tipo_de_union(stmts, refs)
        notes = (
            [] if join_type and by else ["tipo de unión o clave no deducible del MERGE: revisar"]
        )
        status = "soportado" if join_type and by else "parcial"
        join = b.op(
            "join",
            {
                "by": [n.lower() for n in by],
                "join_type": join_type,
                "sources": [qualify(r["name"]) for r in refs],
            },
            ev,
            status=status,
            notes=notes,
        )
        for read in entradas:
            b.link(read, join)
        return reads, join
    if len(reads) > 1:
        union = b.op("union", {"sources": [qualify(r["name"]) for r in refs]}, ev)
        for read in entradas:
            b.link(read, union)
        return reads, union
    return reads, entradas[0] if refs and refs[0].get("where") else None


def lower_data(step: DataStep, ev: Evidence, b: Builder) -> None:
    """Pasos de un DATA step a operadores. Las declaraciones de tipo (length, format,
    informat) se guardan en las derivaciones del paso (`declared`), para la pasada 9."""
    start = len(b.created)
    _lower_data_steps(step, ev, b)
    declarations = [
        (s.fields["declaration"], s.text.split(None, 1)[1] if " " in s.text else "")
        for s in step.statements
        if s.kind == "declare"
    ]
    declared = declared_types(declarations)
    if declared:
        for op in b.created[start:]:
            if op.kind == "derive":
                op.params["declared"] = {k: [v.type, v.length] for k, v in declared.items()}
                b.refresh(op)


def _lower_data_steps(step: DataStep, ev: Evidence, b: Builder) -> None:
    busqueda = detectar_busqueda(step.statements)  # FIND de un hash como unir izquierdo (B-21)
    if busqueda is not None:
        step = busqueda.paso(step)
    stmts = step.statements
    reads, current = _lower_sources(stmts, ev, b)
    if any(
        read.status == "hueco"
        and str(read.params.get("pending_code", "")).startswith("P-LIBNAME-")
        for read in reads
    ):
        # No hay flujo de entrada al que aplicar WHERE/KEEP ni salida que se pueda emitir.
        return
    file_read = _read_file(stmts, ev, b)
    if file_read is not None and (current is not None or reads):
        file_read.params["reason"] = "LECTURAS_DATA_STEP_MIXTAS"
        file_read.status = "hueco"
        file_read.notes.append(
            "SET/MERGE y INFILE/INPUT coexisten; revisar el orden de lectura SAS"
        )
        b.refresh(file_read)
        b.link(current or reads[0], file_read)
        current = file_read
    elif current is None:
        current = file_read or (reads[0] if reads else None)
    if busqueda is not None and current is not None:
        current = busqueda.unir(current, ev, b)
    pending_derive: Operator | None = None
    loose: list[str] = []
    prev: DsStatement | None = None
    omit: set[int] = set()
    destinos_invalidos = _undeclared_output_targets(stmts, step.outputs)
    destinos_repetidos = _repeated_output_targets(stmts, step.outputs)
    paso_output_invalido = destinos_invalidos is not None or destinos_repetidos is not None
    if paso_output_invalido:
        if destinos_invalidos is not None:
            sentencias, faltantes = destinos_invalidos
            reason_detail = "OUTPUT_DESTINO_NO_DECLARADO"
            nombres = ", ".join(sorted(faltantes))
            mensaje = f"OUTPUT nombra destinos ausentes del encabezado DATA: {nombres}"
        elif destinos_repetidos is not None:
            sentencias, repetidos = destinos_repetidos
            reason_detail = "OUTPUT_DESTINO_REPETIDO"
            nombres = ", ".join(sorted(repetidos))
            mensaje = f"OUTPUT escribe más de una vez en el mismo destino: {nombres}"
        evidencia_salida = _statement_evidence(sentencias[0], ev)
        pendiente = b.op(
            "unsupported",
            {
                "reason": "SENTENCIA_NO_SOPORTADA",
                "reason_detail": reason_detail,
                "statement": " | ".join(sentencia.text for sentencia in sentencias),
            },
            evidencia_salida,
            status="hueco",
            notes=[mensaje],
        )
        if current is not None:
            b.link(current, pendiente)
        current = pendiente
        omit = set(range(len(stmts)))
    grupo = programa_por_grupo(stmts)
    if grupo is not None and not paso_output_invalido:
        # BY con FIRST./LAST./RETAIN/suma: un programa por fila con estado, no sentencias sueltas.
        estado = b.op("stateful_row", grupo, ev)
        if current is not None:
            b.link(current, estado)
        current = estado
        omit = set(range(len(stmts)))
    recorrido = _Recorrido(step, ev, b, current, omit, pending_derive, loose, prev)
    recorrido.ejecutar()
    current = recorrido.current
    loose = recorrido.loose
    outputs = step.outputs
    if current is None:
        current = b.op(
            "derive",
            {"assignments": []},
            ev,
            status="parcial",
            notes=["DATA step sin entradas ni sentencias traducibles"],
        )
    if loose:
        current.params.setdefault("untranslated", []).extend(loose)
        b.refresh(current)
    if "_null_" in [o.lower() for o in outputs]:
        current.notes.append("salida _NULL_: no escribe dataset")
    salidas_explicitas = [statement for statement in step.statements if statement.kind == "output"]
    if (
        len(salidas_explicitas) == 1
        and current.kind == "split"
        and not salidas_explicitas[0].fields.get("targets")
    ):
        destinos = [qualify(nombre) for nombre in outputs if nombre.lower() != "_null_"]
        if destinos:
            current.params["target"] = destinos[0]
            current.params["condition"] = ""
            current.params.pop("branch", None)
            if len(destinos) > 1:
                current.params["targets"] = destinos
            else:
                current.params.pop("targets", None)
            current.status = "soportado"
            current.notes = [
                nota
                for nota in current.notes
                if "OUTPUT sin destino explícito" not in nota
            ]
            b.refresh(current)
    # OUTPUT explícito suprime la escritura implícita al final de cada iteración SAS.
    # Sus operadores split son los únicos productores de las tablas de salida.
    if any(
        statement.kind == "output" or _conditional_output(statement) is not None
        for statement in step.statements
    ):
        if not (current.kind == "map" and current.params.get("branches")):
            current.params["outputs"] = []
    else:
        current.params["outputs"] = [qualify(o) for o in outputs if o.lower() != "_null_"]
    b.refresh(current)
