"""Pasos DATA a operadores lógicos: lecturas, filtros, derivaciones, uniones y estado por fila."""

from __future__ import annotations

import re
from dataclasses import replace

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_data_bloques import bloque_condicional
from sgm.ir.lower_data_grupos import programa_por_grupo
from sgm.ir.models import Evidence, Operator
from sgm.ir.types_code import declared_types

_HEAD_KINDS = frozenset({"set", "merge", "by", "infile", "input", "datalines"})
_IF_ASSIGN = re.compile(r"(?is)^if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_IF_ASSIGN = re.compile(r"(?is)^else\s+if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_ASSIGN = re.compile(r"(?is)^else\s+([\w]+)\s*=\s*(.+)$")


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


def _statement_evidence(stmt: DsStatement, ev: Evidence) -> Evidence:
    return replace(
        ev, file=stmt.file or ev.file, line_start=stmt.line, line_end=stmt.end_line or stmt.line
    )


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
    destinos_repetidos = _repeated_output_targets(stmts)
    condicionales_no_terminales = _nonterminal_conditional_outputs(stmts)
    paso_output_invalido = any(
        problema is not None
        for problema in (destinos_invalidos, destinos_repetidos, condicionales_no_terminales)
    )
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
        else:
            sentencias = condicionales_no_terminales or []
            reason_detail = "OUTPUT_CONDICIONAL_NO_TERMINAL"
            mensaje = (
                "OUTPUT condicional seguido de más sentencias requiere preservar "
                "el flujo restante"
            )
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
    for index, s in enumerate(stmts):
        if index in omit:
            continue
        kind = s.kind
        statement_ev = Evidence(ev.file, s.line, s.line, ev.label, ev.call)
        before, prev = prev, s
        if kind in _HEAD_KINDS:
            continue
        secuencia_output = _output_sequence(stmts, index)
        if secuencia_output is not None:
            destinos, ultimo = secuencia_output
            parametros = {"target": destinos[0], "condition": ""}
            if len(destinos) > 1:
                parametros["targets"] = destinos
            salida_multiple = b.op("split", parametros, statement_ev)
            salida_multiple.evidence.extend(
                Evidence(ev.file, stmts[posicion].line, stmts[posicion].line, ev.label, ev.call)
                for posicion in range(index + 1, ultimo + 1)
            )
            if current is not None:
                b.link(current, salida_multiple)
            current = salida_multiple
            omit.update(range(index + 1, ultimo + 1))
            prev = stmts[ultimo]
            continue
        salidas_condicionales = _conditional_output_chain(stmts, index)
        if salidas_condicionales is not None:
            ramas, destinos, siguiente = salidas_condicionales
            salida_condicional = b.op(
                "map",
                {"steps": [], "outputs": destinos, "branches": ramas},
                statement_ev,
            )
            salida_condicional.evidence.extend(
                Evidence(ev.file, stmts[posicion].line, stmts[posicion].line, ev.label, ev.call)
                for posicion in range(index + 1, siguiente + 1)
                )
            if current is not None:
                b.link(current, salida_condicional)
            current = salida_condicional
            omit.update(range(index + 1, siguiente + 1))
            prev = stmts[siguiente]
            continue
        conditional = _conditional_assignment(stmts, index)
        if conditional is not None:
            conditional = ([conditional[0]], conditional[1])
        else:
            conditional = bloque_condicional(stmts, index)
        if conditional is not None:
            asignaciones, siguiente = conditional
            if pending_derive is None:
                pending_derive = b.op(
                    "derive", {"assignments": [], "modo": "agrega"}, statement_ev
                )
                if current is not None:
                    b.link(current, pending_derive)
                current = pending_derive
            pending_derive.params["assignments"].extend(asignaciones)
            b.refresh(pending_derive)
            omit.update(range(index + 1, siguiente))
            prev = stmts[siguiente - 1]
            continue
        if kind == "assign":
            assignment = {"target": s.fields["target"], "expression": s.fields["expression"]}
            if pending_derive is None:
                # `modo`: una asignación de DATA step conserva las columnas que ya venían; el
                # `derive` de un `SELECT` las reemplaza. Sin la marca, el emisor escribiría un
                # `tMap` con una sola columna y el Job perdería el resto de la fila.
                pending_derive = b.op(
                    "derive", {"assignments": [], "modo": "agrega"}, statement_ev
                )
                if current is not None:
                    b.link(current, pending_derive)
                current = pending_derive
            pending_derive.params["assignments"].append(assignment)
            origin = _statement_evidence(s, ev)
            path = ("assignments", len(pending_derive.params["assignments"]) - 1, "expression")
            pending_derive.expression_evidence[path] = [origin]
            b.refresh(pending_derive)
            continue
        pending_derive = None
        if kind == "declare":
            _note(current, f"declaración sin efecto en la lógica: {s.text}")
            continue
        if kind in ("array", "do", "end"):
            _note(current, f"{kind} no traducido: revisar el bucle o el arreglo", status="parcial")
            continue
        if kind in ("file", "put"):
            if current is not None and current.kind != "unsupported":
                note = f"FILE_PUT_SIN_PLANTILLA: {s.text}"
                if note not in current.notes:
                    current.notes.append(note)
                unsupported = b.op(
                    "unsupported",
                    {
                        "reason": "SENTENCIA_NO_SOPORTADA",
                        "reason_detail": "FILE_PUT_SIN_PLANTILLA",
                        "unsupported_statements": [s.text],
                        "statement": s.text,
                    },
                    statement_ev,
                    status="hueco",
                )
                b.link(current, unsupported)
                current = unsupported
            elif current is None:
                current = b.op(
                    "unsupported",
                    {
                        "reason": "SENTENCIA_NO_SOPORTADA",
                        "reason_detail": "FILE_PUT_SIN_PLANTILLA",
                        "unsupported_statements": [s.text],
                        "statement": s.text,
                    },
                    statement_ev,
                    status="hueco",
                )
            else:
                note = f"FILE_PUT_SIN_PLANTILLA: {s.text}"
                if note not in current.notes:
                    current.notes.append(note)
                unsupported = current.params.setdefault("unsupported_statements", [])
                if s.text not in unsupported:
                    unsupported.append(s.text)
                    current.params["statement"] = " | ".join(unsupported)
                    b.refresh(current)
            continue
        new = _statement_op(s, kind, before, statement_ev, b)
        if new is None:
            _note(current, f"sentencia sin traducción: {s.text}", status="parcial")
            if current is not None:
                current.params.setdefault("untranslated", []).append(s.text)
                b.refresh(current)
            else:
                loose.append(s.text)  # sin operador aún: se adjunta al operador final
            continue
        if new.kind == "filter":
            origin = _statement_evidence(s, ev)
            new.expression_evidence[("expression",)] = [origin]
        if current is not None:
            b.link(current, new)
        current = new
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
    if any(statement.kind == "output" for statement in step.statements):
        if not (current.kind == "map" and current.params.get("branches")):
            current.params["outputs"] = []
    else:
        current.params["outputs"] = [qualify(o) for o in outputs if o.lower() != "_null_"]
    b.refresh(current)


def _conditional_assignment(
    stmts: list[DsStatement], index: int
) -> tuple[dict, int] | None:
    """Combina ramas de asignación con destino común.

    SAS exige que ELSE siga inmediatamente al IF-THEN; se conserva esa condición del lenguaje
    (`lestmtsref`, p. 132-133) y no se emparejan ramas separadas por otras sentencias.
    """
    current = stmts[index]
    if current.kind != "if":
        return None
    first = _IF_ASSIGN.fullmatch(current.text.strip())
    if first is None:
        return None
    target = first.group(2).lower()
    branches = [{"condition": first.group(1).strip(), "expression": first.group(3).strip()}]
    cursor = index + 1
    while cursor < len(stmts):
        else_if = _ELSE_IF_ASSIGN.fullmatch(stmts[cursor].text.strip())
        if else_if is None:
            break
        if else_if.group(2).lower() != target:
            return None
        branches.append(
            {"condition": else_if.group(1).strip(), "expression": else_if.group(3).strip()}
        )
        cursor += 1
    if cursor >= len(stmts):
        return None
    otherwise = _ELSE_ASSIGN.fullmatch(stmts[cursor].text.strip())
    if otherwise is None or otherwise.group(1).lower() != target:
        return None
    alternativa = otherwise.group(2).strip()
    condicional = (
        {"condition": branches[0]["condition"], "otherwise": alternativa}
        if len(branches) == 1
        else {"branches": branches, "otherwise": alternativa}
    )
    return (
        {
            "target": target,
            "expression": branches[0]["expression"],
            "conditional": condicional,
        },
        cursor + 1,
    )


def _statement_op(
    s: DsStatement, kind: str, before: DsStatement | None, ev: Evidence, b: Builder
) -> Operator | None:
    """Operador de una sentencia que no es asignación. None si no tiene traducción directa."""
    if kind == "where":
        return b.op("filter", {"expression": s.fields["expression"]}, ev)
    if kind == "if":
        split = _conditional_output(s)
        if split is not None:
            return b.op("split", split, ev)
        if s.fields.get("first_last") or "then" not in s.text.lower():
            if s.fields.get("first_last"):
                return b.op(
                    "stateful_row",
                    {"reason": "first_last", "text": s.text},
                    ev,
                    status="parcial",
                    notes=["lógica de grupo por first./last.: revisar"],
                )
            return b.op("filter", {"expression": re.sub(r"(?i)^if\s+", "", s.text)}, ev)
        return b.op(
            "derive",
            {"conditional": s.text},
            ev,
            status="parcial",
            notes=["asignación condicional: traducir como expresión condicional"],
        )
    if kind in ("keep", "drop"):
        return b.op("select", {"mode": kind, "names": [n.lower() for n in s.fields["names"]]}, ev)
    if kind == "rename":
        return b.op("rename", {"pairs": [[a.lower(), c.lower()] for a, c in s.fields["pairs"]]}, ev)
    if kind == "output":
        condition = before.text if before is not None and before.kind == "if" else ""
        targets = s.fields.get("targets") or []
        target = targets[0] if targets else None
        params = {"target": target, "condition": condition}
        if len(targets) > 1:
            params["targets"] = targets
        return b.op(
            "split",
            params,
            ev,
            status="soportado" if target else "parcial",
            notes=(
                []
                if target
                else ["OUTPUT sin destino explícito requiere semántica de salida por defecto"]
            ),
        )
    if kind in ("retain", "lag", "call_symput"):
        notes = ["estado entre filas: en Talend requiere tJavaRow o tMap con variables"]
        return b.op(
            "stateful_row", {"reason": kind, "text": s.text}, ev, status="parcial", notes=notes
        )
    return None


_OUTPUT_IN_IF = re.compile(
    r"(?is)^(?:if\s+(?P<cond>.*?)\s+then\s+|else\s+if\s+(?P<else_if>.*?)\s+then\s+|else\s+)"
    r"output\s+(?P<targets>[\w.&]+(?:\s+[\w.&]+)*)"
)


def _conditional_output(s: DsStatement) -> dict | None:
    """`if c then output t;` o `else output t;` como división. None si no aplica."""
    m = _OUTPUT_IN_IF.match(s.text.strip())
    if not m:
        return None
    cond = m.group("cond") or m.group("else_if")
    targets = re.findall(r"[\w.&]+", m.group("targets"))
    result = {
        "target": targets[0] if targets else None,
        "condition": cond.strip() if cond else None,
        "branch": "then" if m.group("cond") else "else_if" if m.group("else_if") else "else",
    }
    if len(targets) > 1:
        result["targets"] = targets
    return result


def _conditional_output_chain(
    stmts: list[DsStatement], index: int
) -> tuple[list[dict], list[str], int] | None:
    """Agrupa un IF/ELSE IF/ELSE de OUTPUT terminal en ramas mutuamente excluyentes."""
    primera = _conditional_output(stmts[index])
    if primera is None or primera.get("branch") != "then" or not primera.get("condition"):
        return None
    alternativas = [(str(primera["condition"]), primera.get("targets", [primera["target"]]))]
    cursor = index + 1
    hay_else = False
    while cursor < len(stmts):
        siguiente = _conditional_output(stmts[cursor])
        if siguiente is None:
            break
        if siguiente.get("branch") == "else_if" and not hay_else:
            alternativas.append(
                (str(siguiente["condition"]), siguiente.get("targets", [siguiente["target"]]))
            )
            cursor += 1
            continue
        if siguiente.get("branch") == "else" and not hay_else:
            alternativas.append(("", siguiente.get("targets", [siguiente["target"]])))
            hay_else = True
            cursor += 1
        break
    if cursor <= index + 1 or cursor != len(stmts):
        return None
    destinos = [destino for _condicion, objetivos in alternativas for destino in objetivos]
    if any(not destino or destino.lower() == "_null_" for destino in destinos):
        return None
    if len({destino.lower() for destino in destinos}) != len(destinos):
        return None
    condiciones = [condicion for condicion, _objetivos in alternativas if condicion]
    ramas: list[dict] = []
    anteriores: list[str] = []
    for condicion, objetivos in alternativas:
        if condicion:
            predicados = [*(f"not ({anterior})" for anterior in anteriores), f"({condicion})"]
            expresion_rama = " and ".join(predicados)
            anteriores.append(condicion)
        else:
            expresion_rama = " and ".join(f"not ({anterior})" for anterior in condiciones)
        ramas.extend(
            {"expression": expresion_rama, "outputs": [qualify(destino)]}
            for destino in objetivos
        )
    return ramas, [qualify(destino) for destino in destinos], cursor - 1


def _nonterminal_conditional_outputs(stmts: list[DsStatement]) -> list[DsStatement] | None:
    """Una rama condicional solo es segura si es un OUTPUT simple terminal o cadena terminal."""
    indices = [index for index, stmt in enumerate(stmts) if _conditional_output(stmt)]
    if not indices:
        return None
    if (
        len(indices) == 1
        and indices[0] == len(stmts) - 1
        and (_conditional_output(stmts[indices[0]]) or {}).get("branch") == "then"
    ):
        return None
    if _conditional_output_chain(stmts, indices[0]) is not None:
        return None
    return [stmts[index] for index in indices]


def _output_sequence(stmts: list[DsStatement], index: int) -> tuple[list[str], int] | None:
    """Agrupa OUTPUT consecutivos sin condición ni destinos repetidos."""
    if index >= len(stmts) or stmts[index].kind != "output":
        return None
    destinos: list[str] = []
    cursor = index
    while cursor < len(stmts) and stmts[cursor].kind == "output":
        actuales = stmts[cursor].fields.get("targets") or []
        if not actuales:
            return None
        destinos.extend(nombre for nombre in actuales if nombre.lower() != "_null_")
        cursor += 1
    if cursor - index < 2 or not destinos:
        return None
    if len({nombre.lower() for nombre in destinos}) != len(destinos):
        return None
    return destinos, cursor - 1


def _undeclared_output_targets(
    stmts: list[DsStatement], declared_outputs: list[str]
) -> tuple[list[DsStatement], set[str]] | None:
    """SAS exige destinos declarados en DATA (`lestmtsref`, PDF p. 274; impresa p. 261)."""
    declarados = {qualify(destino).casefold() for destino in declared_outputs}
    sentencias: list[DsStatement] = []
    faltantes: set[str] = set()
    for sentencia in stmts:
        destinos = _output_targets(sentencia)
        no_declarados = {
            destino for destino in destinos if qualify(destino).casefold() not in declarados
        }
        if no_declarados:
            sentencias.append(sentencia)
            faltantes.update(no_declarados)
    return (sentencias, faltantes) if sentencias else None


def _repeated_output_targets(
    stmts: list[DsStatement],
) -> tuple[list[DsStatement], set[str]] | None:
    """Detecta escrituras múltiples al mismo destino en una iteración del DATA step."""
    vistos: dict[str, DsStatement] = {}
    sentencias: list[DsStatement] = []
    repetidos: set[str] = set()
    for sentencia in stmts:
        for destino in _output_targets(sentencia):
            clave = qualify(destino).casefold()
            if clave in vistos:
                if vistos[clave] not in sentencias:
                    sentencias.append(vistos[clave])
                if sentencia not in sentencias:
                    sentencias.append(sentencia)
                repetidos.add(destino)
            else:
                vistos[clave] = sentencia
    return (sentencias, repetidos) if sentencias else None


def _output_targets(stmt: DsStatement) -> list[str]:
    if stmt.kind == "output":
        return list(stmt.fields.get("targets") or [])
    if stmt.kind == "if":
        salida = _conditional_output(stmt)
        if salida:
            destinos = salida.get("targets") or ([salida["target"]] if salida.get("target") else [])
            return list(destinos)
    return []


def _note(op: Operator | None, text: str, status: str | None = None) -> None:
    if op is None:
        return
    op.notes.append(text)
    if status is not None and op.status == "soportado":
        op.status = status
