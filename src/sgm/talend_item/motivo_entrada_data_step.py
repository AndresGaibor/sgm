"""Revisión de equivalencias mínimas para lecturas DATA step delimitadas."""

from __future__ import annotations


def motivo_entrada_data_step(params: dict) -> str | None:
    """Devuelve una razón si el `INFILE/INPUT` podría cambiar datos en Talend."""
    if params.get("multiple_io_statements"):
        return "hay varias sentencias INFILE/INPUT y no se ha modelado su secuencia"
    if params.get("input_mode") != "list":
        return "INPUT posicional o con informat requiere un lector especializado"
    options = params.get("infile_options") or {}
    controles_fin_registro = [
        nombre for nombre in ("flowover", "missover", "truncover") if options.get(nombre)
    ]
    if len(controles_fin_registro) > 1:
        return "FLOWOVER, MISSOVER y TRUNCOVER no pueden combinarse sin fijar su precedencia"
    if options.get("truncover"):
        return "TRUNCOVER en INPUT de lista no tiene equivalencia demostrada"
    if "lrecl" in options:
        return "LRECL cambia el largo físico de los registros"
    if params.get("unsupported_options"):
        return "opciones INFILE sin equivalencia: " + ", ".join(params["unsupported_options"])
    delimiter = params.get("delimiter")
    if delimiter is None and options.get("dsd"):
        delimiter = ","
    if not isinstance(delimiter, str) or len(delimiter) != 1 or delimiter in '\r\n"':
        return "se requiere un DLM explícito de un carácter para igualar la separación"
    firstobs = params.get("firstobs", 1)
    if isinstance(firstobs, bool) or not isinstance(firstobs, int) or firstobs < 1:
        return "FIRSTOBS debe ser un entero positivo"
    if options.get("flowover") or not options.get("missover"):
        return "FLOWOVER permite que INPUT consuma campos de la siguiente línea"
    return None


def codigo_pendiente_entrada_data_step(params: dict, reason: str) -> str:
    """Código específico para opciones de lectura sin equivalencia demostrada."""
    options = params.get("infile_options") or {}
    if reason.startswith("FLOWOVER, MISSOVER"):
        return "P-INFILE-OPCIONES-CONFLICTO"
    if options.get("truncover") and params.get("input_mode") == "list":
        return "P-INFILE-TRUNCOVER-LISTA"
    if reason.startswith("FLOWOVER permite"):
        return "P-INFILE-FLOWOVER"
    return "P-INFILE-SIN-EQUIVALENCIA"


__all__ = ["codigo_pendiente_entrada_data_step", "motivo_entrada_data_step"]
