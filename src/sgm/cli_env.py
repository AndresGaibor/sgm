"""Comandos del entorno de esquemas."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm.catalog import describe as describe_mod

env_app = typer.Typer(help="Entorno: esquemas de las bases.", no_args_is_help=True)


@env_app.command("import-describe")
def env_import_describe(
    archivo: Annotated[Path, typer.Argument(help="Salida de texto de DESCRIBE de Impala.")],
    schema: Annotated[str, typer.Option("--schema", help="Nombre del esquema, en minúsculas.")],
) -> None:
    """Escribe env/schemas/<esquema>.json con las tablas de la salida de DESCRIBE."""
    try:
        ruta, tablas = describe_mod.importar(archivo, schema)
    except (ValueError, FileNotFoundError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Esquema escrito: {ruta} ({len(tablas)} tablas)")
    for tabla, columnas in sorted(tablas.items()):
        sin_tipo = sum(1 for c in columnas if c.type is None)
        typer.echo(f"  {tabla}: {len(columnas)} columnas, {sin_tipo} sin tipo traducible")
