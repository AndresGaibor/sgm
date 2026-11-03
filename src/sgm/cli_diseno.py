"""Comando `sgm diseno`: escribe el diseño de Jobs de cada programa como JSON.

Va aparte de `sgm.cli` para no pasar el límite de 300 líneas del archivo. El diseño es un
artefacto de revisión: no cambia el plan ni la guía.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sgm.batch import compile_batch
from sgm.cli_util import _collect, _env
from sgm.diseno import diseno_de_programa
from sgm.emit.plan_json import metadatos_de_salida


def diseno_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
) -> None:
    """Escribe `<programa>.diseno.json`: joblets por grupo, contexto y Job padre."""
    if not source.exists():
        raise typer.BadParameter(f"no existe: {source}")
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    compiled, _ = compile_batch(files, workers=1, env=_env())
    for program, result in compiled.items():
        payload = {
            "metadatos": metadatos_de_salida(),
            **diseno_de_programa(program, files[program], result.plan),
        }
        stem = Path(program).with_suffix("").as_posix().replace("/", "__")
        destino = out / f"{stem}.diseno.json"
        destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        padre = payload["job_padre"]
        nodos = padre["nodos"]
        firmas = payload["firmas_de_componente"]
        typer.echo(
            f"{program}: {len(payload['joblets'])} joblets, {nodos} nodos en el Job padre, "
            f"{firmas} firmas de componente"
        )
    typer.echo(f"Salida en {out}")
