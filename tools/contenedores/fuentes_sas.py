"""Extrae tablas base y fuentes omitidas de un programa SAS."""

from dataclasses import dataclass
from pathlib import Path

from sgm.migrar.esquemas_programa import _detalle_fuentes
from sgm.migrar.esquemas_programa import _nombre_literal as _nombre_literal


@dataclass(frozen=True)
class TablaBase:
    """Tabla que el programa lee de una biblioteca."""

    biblioteca: str
    tabla: str
    columnas: tuple[str, ...]


@dataclass(frozen=True)
class Omitida:
    """Fuente que no se puede crear sin más información, con su motivo."""

    nombre: str
    motivo: str


def tablas_base(ruta_sas: Path) -> tuple[list[TablaBase], list[Omitida]]:
    """Devuelve las tablas base del programa y las fuentes omitidas con su motivo."""
    texto = ruta_sas.read_text(encoding="utf-8", errors="replace")
    vistas, omitidas = _detalle_fuentes(texto, str(ruta_sas), False)
    return (
        [TablaBase(*clave.split("."), tuple(columnas)) for clave, columnas in vistas.items()],
        [Omitida(nombre, motivo) for nombre, motivo in omitidas],
    )
