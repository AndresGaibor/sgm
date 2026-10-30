"""CLI de sgm."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sgm import cache
from sgm import decisions as decisions_mod
from sgm import diagnostics as diagnostics_mod
from sgm import lineage as lineage_mod
from sgm import metrics as metrics_mod
from sgm.batch import compile_batch
from sgm.catalog.config import ConfigError, Env, load_env
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


def _env() -> Env:
    """`env/` cargado y validado. Un archivo mal formado detiene el comando con su mensaje."""
    try:
        return load_env()
    except ConfigError as error:
        typer.echo(f"Configuración no válida: {error}", err=True)
        raise typer.Exit(code=2) from error


def _project_name(source: Path) -> str:
    return source.stem if source.is_file() else source.name


def _write_outputs(out: Path, compiled: dict) -> list[str]:
    """Escribe guía y plan de cada programa. Devuelve los nombres escritos."""
    names: list[str] = []
    for program, result in compiled.items():
        stem = Path(program).with_suffix("").as_posix().replace("/", "__")
        guide = f"{stem}.guide.md"
        plan = f"{stem}.plan.json"
        (out / guide).write_text(render_guide(result.plan), encoding="utf-8")
        payload = plan_to_dict(result.plan)
        (out / plan).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        names += [guide, plan]
    return names


@app.command()
def compile(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    workers: Annotated[int, typer.Option("--workers", help="Programas en paralelo.")] = 1,
    no_cache: Annotated[bool, typer.Option("--no-cache", help="No usar la caché.")] = False,
) -> None:
    """Escribe `<programa>.guide.md` y `<programa>.plan.json` por cada programa."""
    if not source.exists():
        raise typer.BadParameter(f"no existe: {source}")
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    key = cache.project_key(files)
    if not no_cache:
        restored = cache.restore(out, key)
        if restored:
            typer.echo(f"Caché: {len(restored)} archivos recuperados sin recalcular.")
            return
    compiled, _ = compile_batch(files, workers=workers, env=_env())
    project = _project_name(source)
    with Store() as store:
        for result in compiled.values():
            override_store.apply(result.plan, store, project)
        gap_store.save(store, gap_store.inventory([r.plan for r in compiled.values()]))
    names = _write_outputs(out, compiled)
    for program, result in compiled.items():
        typer.echo(
            f"{program}: {len(result.plan.graph)} operadores, "
            f"{len(result.plan.gaps)} firmas con hueco"
        )
    cache.save(out, key, names)
    typer.echo(f"Salida en {out}")


@app.command()
def metrics(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
) -> None:
    """Imprime las métricas y las guarda en `out/metrics.json` y `out/diagnostico.md`."""
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    compiled, analysis = compile_batch(files, env=_env())
    report = metrics_mod.compute(compiled, files, analysis)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "diagnostico.md").write_text(
        diagnostics_mod.render(diagnostics_mod.build(compiled), report), encoding="utf-8"
    )
    total = report["total"]
    typer.echo(
        f"Programas {total['programas']}, pasos SAS {total['pasos_sas']}, "
        f"nodos SAS {total['nodos_sas']}, componentes {total['componentes']}, "
        f"pasos por componente {total['pasos_por_componente']}, "
        f"nodos por componente {total['nodos_por_componente']}, tJava {total['pct_tjava']} %"
    )
    typer.echo(f"Métricas en {out / 'metrics.json'} y diagnóstico en {out / 'diagnostico.md'}")


@app.command()
def lineage(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
) -> None:
    """Propone oleadas de ejecución según las tablas permanentes que escribe y lee cada programa."""
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    compiled, _ = compile_batch(files, env=_env())
    for number, wave in enumerate(lineage_mod.waves(compiled), 1):
        typer.echo(f"Oleada {number}: " + ", ".join(wave))


@decisions_app.command("pendientes")
def decisions_pending(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    top: Annotated[int, typer.Option("--top", help="Cuántas firmas mostrar.")] = 30,
) -> None:
    """Decisiones pendientes agrupadas por firma: cuántos operadores y archivos la comparten."""
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    compiled, _ = compile_batch(files, env=_env())
    totals = decisions_mod.totals(compiled)
    typer.echo(f"{totals['decisiones']} decisiones, {totals['firmas']} firmas únicas")
    for group in decisions_mod.group(compiled)[:top]:
        options = ", ".join(group.options)
        typer.echo(
            f"{group.signature}  operadores={group.operators}  archivos={len(group.files)}  "
            f"opciones=[{options}]  por_defecto={group.default}"
        )


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


if __name__ == "__main__":
    app()
