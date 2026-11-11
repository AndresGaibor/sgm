"""Comandos `sgm studio`: salud, compilación en lote y verificación de Jobs.

El backend se elige explícitamente. `mcp` (por omisión) habla con el servidor MCP ya arrancado;
`talend` usa la CLI y exige `--talend-dir` y `--proyecto`. Ninguno de los dos escribe Jobs:
`sgm talend` y `sgm migrar` siguen siendo los que los emiten.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer

from sgm.backend_talend import (
    BackendNoDisponible,
    BackendTalend,
    McpBackend,
    TalendCliBackend,
)
from sgm.backend_talend.salud import comprobar_salud

studio_app = typer.Typer(
    help="Studio: salud, compilación en lote y verificación por MCP o CLI.", no_args_is_help=True
)

_BACKEND = Annotated[
    str, typer.Option("--backend", help="mcp (servidor ya arrancado) o talend (CLI de Talend).")
]
_URL = Annotated[
    str | None,
    typer.Option("--url", help="URL del MCP; por omisión, la configurada en el entorno."),
]
_TALEND_DIR = Annotated[
    Path | None, typer.Option("--talend-dir", help="Carpeta de la CLI de Talend.")
]
_PROYECTO = Annotated[
    Path | None,
    typer.Option("--proyecto", help="Carpeta del proyecto Talend para el backend talend."),
]
_TIEMPO = Annotated[float, typer.Option("--tiempo-max", help="Segundos de espera.")]


def _ruta_entorno(nombre: str) -> Path | None:
    """Ruta de una variable de entorno, si está y no viene vacía."""
    valor = os.environ.get(nombre)
    return Path(valor) if valor else None


def _elegir_backend(
    opcion: str,
    url: str | None,
    talend_dir: Path | None,
    proyecto: Path | None,
    tiempo_max: float,
) -> BackendTalend:
    """Backend pedido, o `BadParameter` si al de CLI le faltan sus dos rutas."""
    if opcion == "mcp":
        return McpBackend(url=url, tiempo_max=tiempo_max)
    if opcion != "talend":
        raise typer.BadParameter(f"backend desconocido: {opcion!r}; usa mcp o talend")
    talend_dir = talend_dir or _ruta_entorno("SGM_TALEND_DIR")
    proyecto = proyecto or _ruta_entorno("SGM_TALEND_PROJECT")
    if talend_dir is None or proyecto is None:
        raise typer.BadParameter(
            "el backend talend exige --talend-dir y --proyecto "
            "(o SGM_TALEND_DIR y SGM_TALEND_PROJECT)"
        )
    return TalendCliBackend(talend_dir, proyecto, tiempo_max=tiempo_max)


def _fallo(error: BackendNoDisponible) -> None:
    """Un backend que no responde se informa en una línea, sin traza."""
    typer.echo(f"Studio no está disponible: {error}", err=True)
    raise typer.Exit(code=1) from error


def _contexto(pares: list[str] | None) -> dict[str, str]:
    """`--contexto CLAVE=VALOR` repetido, sin aceptar una forma ambigua."""
    contexto: dict[str, str] = {}
    for par in pares or []:
        if "=" not in par:
            raise typer.BadParameter(f"--contexto espera CLAVE=VALOR: {par!r}")
        clave, valor = par.split("=", 1)
        if not clave:
            raise typer.BadParameter(f"--contexto sin clave: {par!r}")
        contexto[clave] = valor
    return contexto


@studio_app.command("salud")
def salud_command(
    backend: _BACKEND = "mcp",
    url: _URL = None,
    talend_dir: _TALEND_DIR = None,
    proyecto: _PROYECTO = None,
    tiempo_max: _TIEMPO = 10.0,
    recuperar: Annotated[
        bool,
        typer.Option(
            "--recuperar", help="Intenta recuperar Studio una vez si el bridge no responde."
        ),
    ] = False,
) -> None:
    """Comprueba el estado de Studio: si responde, deja escribir y no tiene diálogos abiertos."""
    elegido = _elegir_backend(backend, url, talend_dir, proyecto, tiempo_max)
    salud = comprobar_salud(elegido, tiempo_max, recuperar=recuperar)
    if salud.ok:
        typer.echo(f"Studio responde y deja escribir ({salud.estado}).")
        return
    typer.echo(f"Studio no está disponible ({salud.estado}): {salud.motivo}", err=True)
    raise typer.Exit(code=1)


@studio_app.command("compilar")
def compilar_command(
    jobs: Annotated[list[str], typer.Argument(help="Nombres de los Jobs ya copiados al proyecto.")],
    backend: _BACKEND = "mcp",
    url: _URL = None,
    talend_dir: _TALEND_DIR = None,
    proyecto: _PROYECTO = None,
    refrescar: Annotated[
        bool, typer.Option("--refrescar", help="Releer el workspace antes de compilar.")
    ] = False,
    tiempo_max: _TIEMPO = 120.0,
) -> None:
    """Compila varios Jobs en una llamada e informa el estado de cada uno."""
    if not jobs:
        raise typer.BadParameter("indica al menos un Job")
    elegido = _elegir_backend(backend, url, talend_dir, proyecto, tiempo_max)
    try:
        if refrescar:
            elegido.refrescar()
        resultado = elegido.compilar_lote(list(jobs))
    except BackendNoDisponible as error:
        _fallo(error)
    for nombre in resultado.compilan:
        typer.echo(f"OK {nombre}")
    for nombre, motivo in resultado.no_compilan.items():
        typer.echo(f"FALLA {nombre}: {motivo}", err=True)
    if resultado.no_compilan:
        raise typer.Exit(code=1)


@studio_app.command("verificar")
def verificar_command(
    job: Annotated[str, typer.Argument(help="Nombre del Job ya compilado.")],
    contexto: Annotated[
        list[str] | None,
        typer.Option("--contexto", help="Variable CLAVE=VALOR; se puede repetir."),
    ] = None,
    backend: _BACKEND = "mcp",
    url: _URL = None,
    talend_dir: _TALEND_DIR = None,
    proyecto: _PROYECTO = None,
    tiempo_max: _TIEMPO = 600.0,
) -> None:
    """Verifica un Job: compila, revisa el diseño y devuelve su veredicto."""
    elegido = _elegir_backend(backend, url, talend_dir, proyecto, tiempo_max)
    try:
        veredicto = elegido.verificar(job, _contexto(contexto))
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error
    except BackendNoDisponible as error:
        _fallo(error)
    typer.echo(f"Veredicto: {veredicto.nivel}")
    for hallazgo in veredicto.hallazgos:
        typer.echo(f"  {hallazgo}")
    if veredicto.nivel == "error":
        raise typer.Exit(code=1)


__all__ = ["studio_app"]
