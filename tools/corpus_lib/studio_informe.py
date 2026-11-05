"""Informe Markdown de la comparación de un caso con la salida de Studio (o de una carpeta).

La tabla tiene una fila por caso: si coincide, cuántas diferencias hay, qué archivos faltan y
cuáles sobran. Debajo, las diferencias concretas de cada caso que no coincide, con un límite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .caso import Caso
from .studio_comparar import ResultadoArchivo, comparar_carpetas

MAXIMO_DIFERENCIAS = 30


@dataclass
class ResultadoCaso:
    """Comparación de un caso. `error` explica por qué no se pudo comparar (Studio, lectura)."""

    caso: str
    archivos: list[ResultadoArchivo] = field(default_factory=list)
    error: str = ""

    @property
    def coincide(self) -> bool:
        return not self.error and bool(self.archivos) and all(a.coincide for a in self.archivos)


def comparar_caso(
    caso: Caso, salida: Path, *, error: str = "", ignorar_orden_columnas: bool = False
) -> ResultadoCaso:
    """Compara la salida con `esperado/` del caso, con su tolerancia y su orden.

    Si la ejecución falló sin dejar salida, solo queda el error. Si dejó salida, se compara igual
    y el error acompaña al resultado: un Job que termina mal no puede dar "coincide".
    """
    sin_salida = not salida.is_dir() or not any(salida.glob("*.csv"))
    if error and sin_salida:
        return ResultadoCaso(caso.nombre, error=error)
    archivos = comparar_carpetas(
        caso.esperado,
        salida,
        tolerancia=caso.tolerancia,
        orden_relevante=caso.orden_relevante,
        ignorar_orden_columnas=ignorar_orden_columnas,
    )
    if not archivos:
        return ResultadoCaso(
            caso.nombre, error=error or f"el caso no tiene CSV en {caso.esperado}"
        )
    return ResultadoCaso(caso.nombre, archivos, error=error)


def _nombres(resultados: list[ResultadoArchivo], estado: str) -> str:
    nombres = [r.nombre for r in resultados if r.estado == estado]
    return ", ".join(nombres) if nombres else "-"


def _estado(resultado: ResultadoCaso) -> str:
    if resultado.error:
        return "error"
    return "coincide" if resultado.coincide else "no coincide"


def tabla_markdown(resultados: list[ResultadoCaso]) -> str:
    """Tabla con una fila por caso, seguida de las diferencias de los que no coinciden."""
    lineas = [
        "| Caso | Resultado | Diferencias | Archivos faltantes | Archivos de más | Error |",
        "|---|---|---:|---|---|---|",
    ]
    for resultado in resultados:
        diferencias = sum(len(a.diferencias) for a in resultado.archivos)
        lineas.append(
            f"| {resultado.caso} | {_estado(resultado)} | {diferencias} "
            f"| {_nombres(resultado.archivos, 'faltante')} "
            f"| {_nombres(resultado.archivos, 'de_mas')} "
            f"| {resultado.error or '-'} |"
        )
    coinciden = sum(1 for r in resultados if r.coincide)
    lineas += ["", f"{len(resultados)} casos, {coinciden} coinciden.", ""]
    for resultado in resultados:
        if resultado.coincide:
            continue
        lineas += _detalle(resultado)
    return "\n".join(lineas) + "\n"


def _detalle(resultado: ResultadoCaso) -> list[str]:
    lineas = [f"## {resultado.caso}", ""]
    if resultado.error:
        lineas += [f"Error: {resultado.error}", ""]
    for archivo in resultado.archivos:
        if archivo.coincide:
            continue
        lineas.append(f"### {archivo.nombre} ({archivo.estado})")
        lineas += [f"- {d.texto()}" for d in archivo.diferencias[:MAXIMO_DIFERENCIAS]]
        restantes = len(archivo.diferencias) - MAXIMO_DIFERENCIAS
        if restantes > 0:
            lineas.append(f"- ... y {restantes} diferencias más")
        lineas.append("")
    return lineas
