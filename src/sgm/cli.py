"""CLI de sgm."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sgm.compile import compile_project
from sgm.emit.guide_md import render_guide
from sgm.emit.plan_json import plan_to_dict
from sgm.ingest.importer import looks_like_sas

app = typer.Typer(
    help="sgm: compila programas SAS a guías de migración Talend.", no_args_is_help=True
)


@app.callback()
def main() -> None:
    """Punto de entrada: cada subcomando es una operación de sgm."""


def _collect(path: Path) -> dict[str, str]:
    """Textos de los programas SAS: un archivo, o todos los de una carpeta (rutas relativas)."""
    if path.is_file():
        return {path.name: path.read_text(encoding="utf-8", errors="replace")}
    files: dict[str, str] = {}
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file() or candidate.suffix.lower() not in {".sas", ".txt"}:
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if candidate.suffix.lower() == ".sas" or looks_like_sas(text):
            files[candidate.relative_to(path).as_posix()] = text
    return files


@app.command()
def compile(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
) -> None:
    """Escribe `<programa>.guide.md` y `<programa>.plan.json` por cada programa."""
    if not source.exists():
        raise typer.BadParameter(f"no existe: {source}")
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    compiled, _ = compile_project(files)
    for program, result in compiled.items():
        stem = Path(program).with_suffix("").as_posix().replace("/", "__")
        (out / f"{stem}.guide.md").write_text(render_guide(result.plan), encoding="utf-8")
        payload = plan_to_dict(result.plan)
        (out / f"{stem}.plan.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        typer.echo(
            f"{program}: {len(result.plan.graph)} operadores, "
            f"{len(result.plan.gaps)} firmas con hueco"
        )
    typer.echo(f"Salida en {out}")
