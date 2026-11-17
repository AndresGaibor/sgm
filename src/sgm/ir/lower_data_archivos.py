"""Reconocimiento acotado de FILE/PUT en un DATA step."""

from __future__ import annotations

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir import operadores
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator
from sgm.ir.pasos import op_validado


def file_put_lista_null(
    step: DataStep,
) -> tuple[DsStatement, DsStatement, dict] | None:
    """Devuelve el contrato probado para DATA _NULL_ con SET y PUT de lista delimitada."""
    if [nombre.casefold() for nombre in step.outputs] != ["_null_"]:
        return None
    file_statements = [statement for statement in step.statements if statement.kind == "file"]
    put_statements = [statement for statement in step.statements if statement.kind == "put"]
    if len(file_statements) != 1 or len(put_statements) != 1:
        return None
    if any(statement.kind not in {"set", "file", "put"} for statement in step.statements):
        return None
    file_statement, put_statement = file_statements[0], put_statements[0]
    file_fields = file_statement.fields
    put_fields = put_statement.fields
    sources = [
        source
        for statement in step.statements
        if statement.kind == "set"
        for source in statement.fields.get("sources", [])
    ]
    variables = put_fields.get("variables", [])
    if (
        not (file_fields.get("es_ruta") or file_fields.get("es_fileref"))
        or file_fields.get("no_reconocidas")
        or put_fields.get("modo") != "lista"
        or not variables
        or len({str(variable).casefold() for variable in variables}) != len(variables)
        or len(sources) != 1
        or sources[0].get("options")
        or any(statement.kind == "merge" for statement in step.statements)
    ):
        return None
    options = file_fields.get("opciones") or {}
    delimiter = str(options.get("dlm") or "")
    if len(delimiter) != 1:
        return None
    params = {
        "inputs": [qualify(str(sources[0]["name"]))],
        "outfile": file_fields["destino"],
        "dbms": "dlm",
        "file_format": "delimited",
        "delimiter": delimiter,
        "putnames": False,
        "dsd": bool(options.get("dsd")),
        "variables": [str(variable).lower() for variable in variables],
        "outputs": [],
    }
    if file_fields.get("es_fileref"):
        params["fileref"] = str(file_fields["fileref"])
    return file_statement, put_statement, params


def escribir_file_put(
    contrato: tuple[DsStatement, DsStatement, dict],
    statement_ev: Evidence,
    builder: Builder,
) -> Operator:
    """Construye la salida de archivo validando su forma común de escritura."""
    file_statement, _, params = contrato

    def construir() -> Operator:
        escritura = operadores.escribir_archivo(
            "_",
            params["inputs"],
            params["outfile"],
            dbms=params["dbms"],
            delimiter=params["delimiter"],
            evidence=[statement_ev],
        )
        escritura.params.update(
            {
                key: value
                for key, value in params.items()
                if key not in {"inputs", "outfile", "dbms", "delimiter"}
            }
        )
        return escritura

    escritura = op_validado(builder, construir, "write_file", params, statement_ev)
    escritura.evidence.insert(0, _evidence(file_statement, statement_ev))
    return escritura


def registrar_file_put_pendiente(
    statement: DsStatement,
    statement_ev: Evidence,
    builder: Builder,
    current: Operator | None,
) -> Operator:
    """Conserva el pendiente FILE/PUT y su evidencia dentro de la cadena actual."""
    note = f"FILE_PUT_SIN_PLANTILLA: {statement.text}"
    if current is not None and current.kind != "unsupported":
        if note not in current.notes:
            current.notes.append(note)
        unsupported = builder.op(
            "unsupported",
            {
                "reason": "SENTENCIA_NO_SOPORTADA",
                "reason_detail": "FILE_PUT_SIN_PLANTILLA",
                "unsupported_statements": [statement.text],
                "statement": statement.text,
            },
            statement_ev,
            status="hueco",
        )
        builder.link(current, unsupported)
        return unsupported
    if current is None:
        return builder.op(
            "unsupported",
            {
                "reason": "SENTENCIA_NO_SOPORTADA",
                "reason_detail": "FILE_PUT_SIN_PLANTILLA",
                "unsupported_statements": [statement.text],
                "statement": statement.text,
            },
            statement_ev,
            status="hueco",
        )
    if note not in current.notes:
        current.notes.append(note)
    unsupported = current.params.setdefault("unsupported_statements", [])
    if statement.text not in unsupported:
        unsupported.append(statement.text)
        current.params["statement"] = " | ".join(unsupported)
        builder.refresh(current)
    return current


def _evidence(statement: DsStatement, ev: Evidence) -> Evidence:
    from dataclasses import replace

    return replace(
        ev,
        file=statement.file or ev.file,
        line_start=statement.line,
        line_end=statement.end_line or statement.line,
    )
