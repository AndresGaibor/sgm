"""Comparador de CSV y archivos de texto del corpus a nivel de archivo y de carpeta.

La comparación de filas y celdas está en `studio_filas.py`; aquí se lee cada archivo con
`csv_tabla.leer_csv`, se empareja la carpeta `esperado/` con la salida y se comparan también los
archivos `.txt` por contenido UTF-8 completo, normalizando CRLF/LF al leer.
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
    delimitador: str = ",",
    nombre: str | None = None,
    orden_grupo: list[dict[str, object]] | None = None,
) -> ResultadoArchivo:
    """Compara dos CSV del disco. Un archivo que no se puede leer queda como `ilegible`."""
    nombre = nombre or esperado.name
    try:
        tabla_esperada = leer_csv(esperado, delimitador=delimitador)
        tabla_obtenida = leer_csv(obtenido, delimitador=delimitador)
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
        orden_grupo=orden_grupo,
    )
    return ResultadoArchivo(nombre, "diferente" if diferencias else "coincide", diferencias)


def _csv_por_nombre(carpeta: Path, crudos: set[str] | None = None) -> dict[str, Path]:
    """Archivos `.csv` de la carpeta indexados por nombre en minúsculas, sin extensión."""
    if not carpeta.is_dir():
        return {}
    encontrados: dict[str, Path] = {}
    for ruta in sorted(carpeta.iterdir()):
        if (
            ruta.is_file()
            and ruta.suffix.lower() == ".csv"
            and ruta.name.casefold() not in (crudos or set())
        ):
            encontrados.setdefault(ruta.stem.lower(), ruta)
    return encontrados


def _texto_por_nombre(carpeta: Path, declarados: set[str] | None = None) -> dict[str, Path]:
    """Archivos de texto y archivos declarados cuya salida debe compararse cruda."""
    if not carpeta.is_dir():
        return {}
    return {
        ruta.name.casefold(): ruta
        for ruta in sorted(carpeta.iterdir())
        if ruta.is_file()
        and (ruta.suffix.lower() == ".txt" or ruta.name.casefold() in (declarados or set()))
    }


def _comparar_texto(esperado: Path, obtenido: Path) -> ResultadoArchivo:
    """Compara todo el texto y normaliza únicamente CRLF y CR a LF."""
    try:
        texto_esperado = esperado.read_text(encoding="utf-8")
        texto_obtenido = obtenido.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as fallo:
        return ResultadoArchivo(
            esperado.name,
            "ilegible",
            [Diferencia("archivo", f"no se puede leer como texto UTF-8: {type(fallo).__name__}")],
        )

    def normalizar(texto: str) -> str:
        return texto.replace("\r\n", "\n").replace("\r", "\n")

    igual = normalizar(texto_esperado) == normalizar(texto_obtenido)
    diferencias = [] if igual else [Diferencia("archivo", "el contenido de texto es distinto")]
    return ResultadoArchivo(esperado.name, "coincide" if igual else "diferente", diferencias)


def comparar_carpetas(
    esperado: Path,
    salida: Path,
    *,
    tolerancia: float = 0.0,
    orden_relevante: bool = False,
    ignorar_orden_columnas: bool = False,
    delimitadores: dict[str, str] | None = None,
    archivos_salida: tuple[str, ...] | list[str] = (),
    orden_grupo: list[dict[str, object]] | None = None,
) -> list[ResultadoArchivo]:
    """Empareja cada CSV de `esperado/` con el de la salida con el mismo nombre (sin mayúsculas).

    Un archivo esperado sin par es `faltante`; un archivo de la salida sin esperado es `de_mas`.
    """
    crudos = {nombre.casefold() for nombre in archivos_salida}
    esperados = _csv_por_nombre(esperado, crudos)
    obtenidos = _csv_por_nombre(salida, crudos)
    formatos = {nombre.casefold(): valor for nombre, valor in (delimitadores or {}).items()}
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
                delimitador=formatos.get(clave, ","),
                nombre=ruta.name,
                orden_grupo=orden_grupo,
            )
        )
    for clave, ruta in obtenidos.items():
        if clave not in esperados:
            diferencia = Diferencia("archivo", f"la salida tiene {ruta.name}, que no se espera")
            resultados.append(ResultadoArchivo(ruta.name, "de_mas", [diferencia]))
    esperados_texto = _texto_por_nombre(esperado, crudos)
    obtenidos_texto = _texto_por_nombre(salida, crudos)
    for clave, ruta in esperados_texto.items():
        if clave not in obtenidos_texto:
            diferencia = Diferencia("archivo", f"falta {ruta.name} en la salida")
            resultados.append(ResultadoArchivo(ruta.name, "faltante", [diferencia]))
            continue
        resultados.append(_comparar_texto(ruta, obtenidos_texto[clave]))
    for clave, ruta in obtenidos_texto.items():
        if clave not in esperados_texto:
            diferencia = Diferencia("archivo", f"la salida tiene {ruta.name}, que no se espera")
            resultados.append(ResultadoArchivo(ruta.name, "de_mas", [diferencia]))
    return sorted(resultados, key=lambda r: r.nombre.lower())
