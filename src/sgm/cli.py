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
from sgm.store import gaps as gap_store
from sgm.store import overrides as override_store
from sgm.store.db import Store

app = typer.Typer(
    help="sgm: compila programas SAS a guías de migración Talend.", no_args_is_help=True
)
decisions_app = typer.Typer(
    help="Decisiones del usuario por firma y alcance.", no_args_is_help=True
)
gaps_app = typer.Typer(help="Inventario de huecos.", no_args_is_help=True)
app.add_typer(decisions_app, name="decisions")
app.add_typer(gaps_app, name="gaps")


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


def _project_name(source: Path) -> str:
    return source.stem if source.is_file() else source.name


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
    project = _project_name(source)
    with Store() as store:
        for result in compiled.values():
            override_store.apply(result.plan, store, project)
        gap_store.save(store, gap_store.inventory([r.plan for r in compiled.values()]))
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


@decisions_app.command("list")
def decisions_list() -> None:
    """Muestra las decisiones guardadas."""
    with Store() as store:
        items = override_store.list_overrides(store)
    if not items:
        typer.echo("No hay decisiones guardadas.")
        return
    for o in items:
        ref = f" ref={o.ref}" if o.ref else ""
        typer.echo(f"{o.signature}  {o.option}  alcance={o.scope}{ref}  motivo={o.reason}")


@decisions_app.command("set")
def decisions_set(
    signature: Annotated[str, typer.Argument(help="Firma del operador (la que muestra la guía).")],
    option: Annotated[str, typer.Argument(help="Opción elegida (un componente Talend).")],
    scope: Annotated[
        str, typer.Option("--scope", help="paso, archivo, proyecto o global.")
    ] = "global",
    ref: Annotated[
        str, typer.Option("--ref", help="Nombre del alcance (archivo:línea, archivo, proyecto).")
    ] = "",
    reason: Annotated[str, typer.Option("--reason", help="Motivo de la decisión.")] = "",
) -> None:
    """Guarda una decisión por firma y alcance."""
    try:
        with Store() as store:
            row = override_store.set_override(store, signature, option, scope, ref, reason)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Guardada: {row.signature} -> {row.option} ({row.scope})")


@gaps_app.command("list")
def gaps_list(
    top: Annotated[int, typer.Option("--top", help="Cuántos huecos mostrar.")] = 20,
) -> None:
    """Huecos ordenados por archivos y ocurrencias."""
    with Store() as store:
        rows = gap_store.top(store, top)
    if not rows:
        typer.echo("No hay huecos guardados. Compila primero con `sgm compile`.")
        return
    for row in rows:
        typer.echo(
            f"{row['signature']}  {row['reason']}  archivos={len(row['files'])}  "
            f"ocurrencias={row['occurrences']}"
        )
