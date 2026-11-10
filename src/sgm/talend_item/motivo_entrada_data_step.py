"""Revisión de equivalencias mínimas para lecturas DATA step delimitadas."""

from __future__ import annotations


def motivo_entrada_data_step(params: dict) -> str | None:
    """Devuelve una razón si el `INFILE/INPUT` podría cambiar datos en Talend."""
    if params.get("multiple_io_statements"):
        return "hay varias sentencias INFILE/INPUT y no se ha modelado su secuencia"
    if params.get("input_mode") != "list":
        return "INPUT posicional o con informat requiere un lector especializado"
    options = params.get("infile_options") or {}
    if options.get("dsd"):
        return "DSD cambia el manejo de delimitadores vacíos y comillas"
    if any(name in options for name in ("lrecl", "missover", "truncover")):
        return "LRECL/MISSOVER/TRUNCOVER modifican la lectura de registros"
    if params.get("unsupported_options"):
        return "opciones INFILE sin equivalencia: " + ", ".join(params["unsupported_options"])
    delimiter = params.get("delimiter")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        return "se requiere un DLM explícito de un carácter para igualar la separación"
    firstobs = params.get("firstobs", 1)
    if not isinstance(firstobs, int) or firstobs < 1:
        return "FIRSTOBS debe ser un entero positivo"
    return None


__all__ = ["motivo_entrada_data_step"]
