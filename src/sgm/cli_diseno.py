"""Comando `sgm diseno`: escribe el diseño de Jobs de cada programa como JSON.

Va aparte de `sgm.cli` para no pasar el límite de 300 líneas del archivo. El diseño es un
artefacto de revisión: no cambia el plan ni la guía.

La agrupación de regiones es una decisión del equipo y vive en
`decisiones/<programa>.agrupacion.yaml`. Si el archivo existe se usa; si no, se agrupa por similitud
de conjuntos de datos. El modo usado queda escrito en el JSON y en la salida del comando.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sgm.agrupacion import cargar_declaracion
from sgm.batch import compile_batch
from sgm.cli_util import _collect, _env
from sgm.compile import ROOT_DIR
from sgm.diseno import diseno_de_programa
from sgm.emit.plan_json import metadatos_de_salida

DECISIONES = ROOT_DIR / "decisiones"


def _declaracion(programa: str, ruta: Path | None, carpeta: Path | None = None):
    """Agrupación declarada del programa: la indicada, la de su carpeta o la de `decisiones/`."""
    if ruta is not None:
        return cargar_declaracion(ruta)
    nombre = f"{Path(programa).stem}.agrupacion.yaml"
    candidatos = [p for p in (carpeta / nombre if carpeta else None, DECISIONES / nombre) if p]
    for candidato in candidatos:
        if candidato.exists():
            return cargar_declaracion(candidato)
    return None


def diseno_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    agrupacion: Annotated[
        Path | None,
        typer.Option("--agrupacion", help="YAML con la agrupación declarada por el equipo."),
    ] = None,
) -> None:
    """Escribe `<programa>.diseno.json`: joblets por grupo, contexto y Job padre."""
    if not source.exists():
        raise typer.BadParameter(f"no existe: {source}")
    if agrupacion is not None and not agrupacion.exists():
        raise typer.BadParameter(f"no existe: {agrupacion}")
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    compiled, _ = compile_batch(files, workers=1, env=_env())
    for program, result in compiled.items():
        carpeta = (source if source.is_dir() else source.parent) / Path(program).parent
        try:
            declaracion = _declaracion(program, agrupacion, carpeta)
        except ValueError as error:
            typer.echo(f"Agrupación no válida: {error}", err=True)
            raise typer.Exit(code=2) from error
        payload = {
            "metadatos": metadatos_de_salida(),
            **diseno_de_programa(program, files[program], result.plan, declaracion),
        }
        stem = Path(program).with_suffix("").as_posix().replace("/", "__")
        destino = out / f"{stem}.diseno.json"
        destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        padre = payload["job_padre"]
        nodos = padre["nodos"]
        firmas = payload["firmas_de_componente"]
        modo = payload["agrupacion"]["modo"]
        typer.echo(
            f"{program}: agrupación {modo}, {len(payload['joblets'])} joblets, {nodos} nodos "
            f"en el Job padre, {firmas} firmas de componente"
        )
    typer.echo(f"Salida en {out}")
