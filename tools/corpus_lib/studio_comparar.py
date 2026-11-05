"""Comparador de CSV del corpus a nivel de archivo y de carpeta.

La comparación de filas y celdas está en `studio_filas.py`; aquí se lee cada archivo con
`csv_tabla.leer_csv`, se empareja la carpeta `esperado/` con la salida y se clasifica cada CSV.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .csv_tabla import leer_csv
from .studio_filas import Diferencia, comparar_tablas

__all__ = [
    "Diferencia",
    "ResultadoArchivo",
    "comparar_archivos",
    "comparar_carpetas",
    "comparar_tablas",
]


@dataclass
class ResultadoArchivo:
    """Resultado de comparar un CSV de `esperado/` con su par de la salida.

    `estado`: coincide, diferente, faltante (no está en la salida), de_mas (la salida tiene un
    archivo que el caso no espera) o ilegible (no se puede leer como CSV con encabezado).
    """

    nombre: str
    estado: str
    diferencias: list[Diferencia] = field(default_factory=list)

    @property
    def coincide(self) -> bool:
        return self.estado == "coincide"


def comparar_archivos(
    esperado: Path,
    obtenido: Path,
    *,
    tolerancia: float = 0.0,
    orden_relevante: bool = False,
    ignorar_orden_columnas: bool = False,
    nombre: str | None = None,
) -> ResultadoArchivo:
    """Compara dos CSV del disco. Un archivo que no se puede leer queda como `ilegible`."""
    nombre = nombre or esperado.name
    try:
        tabla_esperada = leer_csv(esperado)
        tabla_obtenida = leer_csv(obtenido)
    except ValueError as fallo:
        return ResultadoArchivo(
            nombre, "ilegible", [Diferencia("archivo", f"no se puede leer: {fallo}")]
        )
    diferencias = comparar_tablas(
        tabla_esperada,
        tabla_obtenida,
        tolerancia=tolerancia,
        orden_relevante=orden_relevante,
        ignorar_orden_columnas=ignorar_orden_columnas,
    )
    return ResultadoArchivo(nombre, "diferente" if diferencias else "coincide", diferencias)


def _csv_por_nombre(carpeta: Path) -> dict[str, Path]:
    """Archivos `.csv` de la carpeta indexados por nombre en minúsculas, sin extensión."""
    if not carpeta.is_dir():
        return {}
    encontrados: dict[str, Path] = {}
    for ruta in sorted(carpeta.iterdir()):
        if ruta.is_file() and ruta.suffix.lower() == ".csv":
            encontrados.setdefault(ruta.stem.lower(), ruta)
    return encontrados


def comparar_carpetas(
    esperado: Path,
    salida: Path,
    *,
    tolerancia: float = 0.0,
    orden_relevante: bool = False,
    ignorar_orden_columnas: bool = False,
) -> list[ResultadoArchivo]:
    """Empareja cada CSV de `esperado/` con el de la salida con el mismo nombre (sin mayúsculas).

    Un archivo esperado sin par es `faltante`; un archivo de la salida sin esperado es `de_mas`.
    """
    esperados = _csv_por_nombre(esperado)
    obtenidos = _csv_por_nombre(salida)
    resultados: list[ResultadoArchivo] = []
    for clave, ruta in esperados.items():
        if clave not in obtenidos:
            diferencia = Diferencia("archivo", f"falta {ruta.name} en la salida")
            resultados.append(ResultadoArchivo(ruta.name, "faltante", [diferencia]))
            continue
        resultados.append(
            comparar_archivos(
                ruta,
                obtenidos[clave],
                tolerancia=tolerancia,
                orden_relevante=orden_relevante,
                ignorar_orden_columnas=ignorar_orden_columnas,
                nombre=ruta.name,
            )
        )
    for clave, ruta in obtenidos.items():
        if clave not in esperados:
            diferencia = Diferencia("archivo", f"la salida tiene {ruta.name}, que no se espera")
            resultados.append(ResultadoArchivo(ruta.name, "de_mas", [diferencia]))
    return sorted(resultados, key=lambda r: r.nombre.lower())
