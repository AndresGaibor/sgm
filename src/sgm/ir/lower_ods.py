"""Detección conservadora de salidas ODS, sin deducir su esquema."""

import re

P_ODS_OUTPUT_DATASET = "P-ODS-OUTPUT-DATASET"
ODS_OUTPUT_NOTE = (
    f"Pendiente: {P_ODS_OUTPUT_DATASET}; ODS OUTPUT produce un dataset cuyo contenido depende "
    "del procedimiento y no está demostrado (proc.pdf, p. 1525)"
)


def writes_dataset(statement: str) -> bool:
    """Exige ODS OUTPUT y un igual fuera de literales, incluidos nombres SAS entre comillas."""
    unquoted = re.sub(r"'([^']|'')*'|\"([^\"]|\"\")*\"", "", statement)
    return bool(re.match(r"(?is)^\s*ods\s+output\b", statement) and "=" in unquoted)
