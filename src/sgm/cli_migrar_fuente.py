"""Nombre y fecha deterministas del programa de origen."""

from datetime import datetime, timezone
from pathlib import Path

from sgm.talend_item.escritura import fecha_studio

# Fecha de los `.properties` si el programa no se puede leer: determinista y sin `fromtimestamp`,
# que falla en Windows por debajo de 1970.
_FECHA_SIN_ARCHIVO = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _nombre(source: Path) -> str:
    """Nombre de la carpeta de salida: el del programa, sin extensión."""
    return source.stem or source.name


def _fecha(source: Path) -> str:
    """Fecha de modificación del programa en el formato de los `.properties`.

    No es la del reloj a propósito: con la fecha del archivo, dos corridas sobre el mismo programa
    dan los mismos bytes y dos migraciones se pueden comparar con `diff`.

    Un programa que no se puede leer no puede tumbar la migración. En Windows
    `datetime.fromtimestamp` levanta `OSError` con marcas por debajo de 1970 —y el respaldo de un
    archivo ilegible era justo la marca 0—, así que la fecha de respaldo se construye sin pasar por
    la marca de tiempo.
    """
    try:
        return fecha_studio(datetime.fromtimestamp(source.stat().st_mtime).astimezone())
    except (OSError, OverflowError, ValueError):
        return fecha_studio(_FECHA_SIN_ARCHIVO)
