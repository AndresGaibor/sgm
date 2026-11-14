"""Intérprete de INFILE con INPUT en lista para el anillo B."""

from __future__ import annotations

import csv
import re
from collections.abc import Sequence

from sgm.migrar.interprete_errores import NoSoportadoEnInterprete


def leer_lista(
    lineas: Sequence[str],
    variables: Sequence[tuple[str, str | None]],
    dlm: str,
    dsd: bool,
    missover: bool,
    firstobs: int = 1,
    truncover: bool = False,
) -> list[dict[str, str | None]]:
    """Lee registros delimitados sin mezclarlos; solo modela opciones demostradas."""
    if not isinstance(dlm, str) or len(dlm) != 1 or dlm in '\r\n"':
        raise NoSoportadoEnInterprete("infile", "P-INFILE-DELIMITADOR")
    if isinstance(firstobs, bool) or not isinstance(firstobs, int) or firstobs < 1:
        raise NoSoportadoEnInterprete("infile", "P-INFILE-FIRSTOBS")
    if truncover:
        raise NoSoportadoEnInterprete("infile", "P-INFILE-TRUNCOVER-LISTA")
    if not missover:
        raise NoSoportadoEnInterprete("infile", "P-INFILE-FLOWOVER")

    rows: list[dict[str, str | None]] = []
    for line in lineas[firstobs - 1 :]:
        try:
            if dsd:
                fields = next(csv.reader([line], delimiter=dlm, quotechar='"', strict=True))
            else:
                fields = re.split(re.escape(dlm) + "+", line)
        except (csv.Error, StopIteration) as error:
            raise NoSoportadoEnInterprete("infile", "P-INFILE-DSD-COMILLAS-INVALIDAS") from error

        values: list[str | None] = []
        for field in fields[: len(variables)]:
            value = field if dsd else field.strip()
            values.append(None if value == "" else value)
        values.extend([None] * (len(variables) - len(values)))
        rows.append(
            {name: value for (name, _informat), value in zip(variables, values, strict=True)}
        )
    return rows


__all__ = ["leer_lista"]
