"""Construcción IR de las lecturas INFILE/INPUT de un DATA step."""

from __future__ import annotations

from sgm.frontend.datastep import DsStatement
from sgm.ir.builder import Builder
from sgm.ir.models import Evidence, Operator
from sgm.ir.types_code import informat_type


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
        elif options.get("dsd"):
            # SAS define coma como separador por omisión de DSD (lestmtsref, INFILE).
            params["delimiter"] = ","
        if isinstance(options.get("firstobs"), int):
            params["firstobs"] = options["firstobs"]
    if input_stmt is not None:
        params["input_mode"] = input_stmt.fields["mode"]
        params["input_names"] = list(input_stmt.fields["names"])
        params["input_statement"] = input_stmt.fields["raw"]
        params["input_line"] = input_stmt.line
        if input_stmt.fields.get("types"):
            params["input_types"] = dict(input_stmt.fields["types"])
        if input_stmt.fields.get("lengths"):
            params["input_lengths"] = dict(input_stmt.fields["lengths"])
        if input_stmt.fields.get("informats"):
            params["input_informats"] = dict(input_stmt.fields["informats"])
        if input_stmt.fields.get("fields"):
            params["input_positions"] = list(input_stmt.fields["fields"])
        if input_stmt.fields.get("informats"):
            type_codes: dict[str, str] = {}
            input_types = dict(params.get("input_types") or {})
            input_lengths = dict(params.get("input_lengths") or {})
            for name, informat in input_stmt.fields["informats"].items():
                declared = informat_type(str(informat))
                if declared is None:
                    continue
                type_codes[str(name)] = declared.type
                if declared.type == "String":
                    input_types[str(name)] = "caracter"
                elif declared.type != "Date":
                    input_types[str(name)] = "numerico"
                if declared.length is not None:
                    input_lengths[str(name)] = declared.length
            params["input_type_codes"] = type_codes
            if input_types:
                params["input_types"] = input_types
            if input_lengths:
                params["input_lengths"] = input_lengths
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
