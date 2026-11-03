"""`sgm facts <ruta>`: imprime en JSON los hechos de un archivo o de una carpeta SAS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sgm.facts.project import facts_for_project


def _leer(ruta: Path) -> dict[str, str]:
    if ruta.is_file():
        return {ruta.name: ruta.read_text(encoding="utf-8-sig", errors="replace")}
    archivos = sorted(p for p in ruta.rglob("*.sas") if p.is_file())
    return {
        p.relative_to(ruta).as_posix(): p.read_text(encoding="utf-8-sig", errors="replace")
        for p in archivos
    }


def facts_command(
    ruta: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    salida: Annotated[
        Path | None, typer.Option("--out", help="Archivo JSON de salida; si no, imprime.")
    ] = None,
) -> None:
    """Hechos de cada programa: tablas, rutas, servidores, macros y sentencias, con fuente."""
    if not ruta.exists():
        raise typer.BadParameter(f"no existe: {ruta}")
    por_archivo = facts_for_project(_leer(ruta))
    datos = {
        archivo: [hecho.to_dict() for hecho in hechos] for archivo, hechos in por_archivo.items()
    }
    texto = json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True)
    if salida:
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(texto + "\n", encoding="utf-8")
        typer.echo(f"hechos escritos en {salida}")
    else:
        typer.echo(texto)


def mapa_command(
    ruta: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    salida: Annotated[
        Path, typer.Option("--out", help="Carpeta donde se escriben los mapas.")
    ] = Path("out") / "mapas",
) -> None:
    """Mapa de flujo en Markdown de cada programa, sin traducir (fase 4.2)."""
    from sgm.facts.mapa import mapa_markdown

    if not ruta.exists():
        raise typer.BadParameter(f"no existe: {ruta}")
    por_archivo = facts_for_project(_leer(ruta))
    salida.mkdir(parents=True, exist_ok=True)
    for archivo, hechos in por_archivo.items():
        nombre = archivo.replace("/", "__").replace("\\", "__")
        (salida / f"{nombre}.md").write_text(
            mapa_markdown(archivo, hechos), encoding="utf-8"
        )
    typer.echo(f"{len(por_archivo)} mapas escritos en {salida}")
