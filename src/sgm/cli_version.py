"""Opción raíz `--version` de la CLI."""

from typing import Annotated

import typer

from sgm import __version__


def _mostrar_version(valor: bool) -> None:
    """Imprime `sgm <versión>` y sale con código 0 cuando se pide la opción."""
    if valor:
        typer.echo(f"sgm {__version__}")
        raise typer.Exit()


VersionOpcion = Annotated[
    bool,
    typer.Option(
        "--version",
        callback=_mostrar_version,
        is_eager=True,
        help="Muestra la versión de sgm y sale.",
    ),
]
