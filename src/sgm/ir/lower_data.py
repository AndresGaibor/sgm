"""Pasos DATA a operadores lógicos: lecturas, filtros, derivaciones, uniones y estado por fila."""

from __future__ import annotations

import re

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_data_grupos import programa_por_grupo
from sgm.ir.lower_data_recorrido import _Recorrido, _statement_evidence
from sgm.ir.lower_data_salidas import (
    _conditional_output,
    _repeated_output_targets,
    _undeclared_output_targets,
)
from sgm.ir.models import Evidence, Operator
from sgm.ir.types_code import declared_types


def _join_type(stmts: list[DsStatement], refs: list[dict]) -> str | None:
    """Tipo de unión de un MERGE según la primera condición `if`. None si no se puede deducir."""
    conditions = [s for s in stmts if s.kind == "if" and s.text.lower().startswith("if ")]
    if not conditions:
        # MERGE sin condición: une todas las filas por llave. No es un JOIN de producto: el
        # intérprete empareja fila con fila dentro de cada grupo (migrar/interprete.py, _mezclar).
        return "full"
    expr = re.sub(r"(?i)^if\s+", "", conditions[0].text).strip()
    expr = re.sub(r"(?i)\s+then\b.*$", "", expr)
    expr = re.sub(r"\s+", " ", expr).strip().lower()
    if len(refs) < 2:
        return None
    first, second = refs[0].get("in"), refs[1].get("in")
    if not first or not second:
        return None
    if expr in (f"{first} and {second}", f"{second} and {first}"):
        return "inner"
    if expr == first:
        return "left"
    if expr == second:
        return "right"
    if expr in (f"{first} or {second}", f"{second} or {first}"):
        return "full"
    return None


def _lower_sources(
    stmts: list[DsStatement], ev: Evidence, b: Builder
) -> tuple[list[Operator], Operator | None]:
    """Lecturas de entrada y la operación que las combina (join, union) si hay más de una."""
    refs: list[dict] = []
    for s in stmts:
        if s.kind in ("set", "merge"):
            refs += [dict(r, mode=s.kind) for r in s.fields["sources"]]
    reads = [
        b.op("read", {"dataset": qualify(r["name"]), "in": (r.get("in") or None)}, ev) for r in refs
    ]
    entradas: list[Operator] = []
    for ref, read in zip(refs, reads, strict=True):
        where = ref.get("where")
        if where:
            filtrado = b.op("filter", {"expression": where}, ev)
            b.link(read, filtrado)
            entradas.append(filtrado)
        else:
            entradas.append(read)
    if any(s.kind == "merge" for s in stmts):
        by = next((s.fields["names"] for s in stmts if s.kind == "by"), [])
        join_type = _join_type(stmts, refs)
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


def _read_file(stmts: list[DsStatement], ev: Evidence, b: Builder) -> Operator | None:
    if not any(s.kind in ("infile", "input", "datalines") for s in stmts):
        return None
    infile = next((s for s in stmts if s.kind == "infile"), None)
    input_stmt = next((s for s in stmts if s.kind == "input"), None)
    datalines = next((s for s in stmts if s.kind == "datalines"), None)
    params: dict = {}
    if infile is not None:
        source = str(infile.fields.get("source") or "")
        if infile.fields.get("source_is_path"):
            params["datafile"] = source
        else:
            params["fileref"] = source
            if infile.fields.get("source_dynamic"):
                params["source_dynamic"] = True
        params["infile_line"] = infile.line
        params["infile_options"] = dict(infile.fields.get("options") or {})
        params["unsupported_options"] = list(infile.fields.get("unsupported_options") or [])
        options = params["infile_options"]
        if options.get("dlm") is not None:
            params["delimiter"] = options["dlm"]
        if isinstance(options.get("firstobs"), int):
            params["firstobs"] = options["firstobs"]
    if input_stmt is not None:
        params["input_mode"] = input_stmt.fields["mode"]
        params["input_names"] = list(input_stmt.fields["names"])
        params["input_statement"] = input_stmt.fields["raw"]
        params["input_line"] = input_stmt.line
        if input_stmt.fields["mode"] != "list":
            params["file_format"] = "positional"
        elif infile is not None:
            params["file_format"] = "delimited"
    if datalines is not None:
        params["datalines_rows"] = datalines.fields.get("rows")
        params["datalines_data"] = list(datalines.fields.get("data") or [])
        params["file_format"] = "datalines"
    if infile is not None:
        params["infile_statement"] = infile.text
    raw_statements = [s.text for s in (infile, input_stmt, datalines) if s is not None]
    if raw_statements:
        params["statement"] = " | ".join(raw_statements)
    status = "soportado"
    if datalines is not None:
        params["reason"] = "DATALINES_SIN_LECTOR"
        status = "hueco"
    elif infile is not None and input_stmt is None:
        params["reason"] = "INFILE_SIN_INPUT"
        status = "hueco"
    elif input_stmt is not None and infile is None:
        params["reason"] = "INPUT_SIN_INFILE"
        status = "hueco"
    if len([s for s in stmts if s.kind == "infile"]) > 1 or len(
        [s for s in stmts if s.kind == "input"]
    ) > 1:
        params["multiple_io_statements"] = True
        if status == "soportado":
            status = "parcial"
    return b.op(
        "read_file",
        params,
        ev,
        status=status,
        notes=["lectura de archivo o de datos en línea del DATA step"],
    )


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
    stmts = step.statements
    reads, current = _lower_sources(stmts, ev, b)
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
