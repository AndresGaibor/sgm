"""Comandos de decisiones y de huecos de la CLI (`sgm decisions ...`, `sgm gaps ...`)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm import decisions as decisions_mod
from sgm import explain as explain_mod  # noqa: F401
from sgm.batch import compile_batch
from sgm.cli_util import _collect, _env
from sgm.store import gaps as gap_store
from sgm.store import overrides as override_store
from sgm.store.db import Store

decisions_app = typer.Typer(
    help="Decisiones del usuario por firma y alcance.", no_args_is_help=True
)
gaps_app = typer.Typer(help="Inventario de huecos.", no_args_is_help=True)


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
            f"opciones=[{options}]  sugerido={group.default} (no aplicado)"
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
    owner: Annotated[str | None, typer.Option("--owner", help="Solo los de este dueño.")] = None,
    file: Annotated[
        str | None,
        typer.Option("--file", help="Solo los que aparecen en un archivo con este texto."),
    ] = None,
) -> None:
    """Huecos ordenados por archivos y ocurrencias, con dueño, arreglo y comando sugerido."""
    with Store() as store:
        rows = gap_store.top(store, top, owner=owner, file=file)
    if not rows:
        if owner or file:
            typer.echo("No hay huecos con esos filtros.")
        else:
            typer.echo("No hay huecos guardados. Compila primero con `sgm compile`.")
        return
    for row in rows:
        example = row["example"] or {}
        typer.echo(
            f"{row['signature']}  {row['reason']}  dueño={row['owner']}  "
            f"archivos={len(row['files'])}  ocurrencias={row['occurrences']}"
        )
        if example:
            typer.echo(
                f"  ejemplo: {example['file']}:{example['line_start']}-{example['line_end']}"
                f"  {example['texto']}"
            )
        typer.echo(f"  se cierra con: {row['fix_with'] or 'sin arreglo registrado'}")
        typer.echo(f"  comando: {row['comando']}")
