"""Comando `sgm flujo`: escribe `<programa>.flujo.html` con cómo funciona cada programa.

Va aparte de `sgm.cli` para no pasar el límite de 300 líneas del archivo. Es una vista de
revisión: no cambia el plan ni la guía.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm.cli_util import _collect, _env
from sgm.flow.model import build_flows
from sgm.flow.page import render_page
from sgm.flow.salida import a_json


def flujo_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    como_json: Annotated[
        bool, typer.Option("--json", help="Escribe también `<programa>.flujo.json`.")
    ] = False,
) -> None:
    """Escribe `<programa>.flujo.html`: pasos en orden, datasets que pasan de uno a otro."""
    if not source.exists():
        raise typer.BadParameter(f"no existe: {source}")
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    env = _env()
    out.mkdir(parents=True, exist_ok=True)
    for program, model in build_flows(files, env.external_files).items():
        stem = Path(program).with_suffix("").as_posix().replace("/", "__")
        destino = out / f"{stem}.flujo.html"
        destino.write_text(render_page(model), encoding="utf-8")
        if como_json:
            out.joinpath(f"{stem}.flujo.json").write_text(a_json(model), encoding="utf-8")
        typer.echo(f"{program}: {len(model.steps)} pasos -> {destino}")
