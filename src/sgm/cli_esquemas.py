"""Comando de propuestas de esquemas desde un programa."""

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from sgm.ir.models import Column
from sgm.migrar.esquemas_programa import a_json, esquemas_desde_programa


def esquemas_command(
    desde_programa: Annotated[Path, typer.Option("--desde-programa", help="Programa SAS.")],
    fixtures: Annotated[
        Path | None, typer.Option("--fixtures", help="Carpeta con fichas de fixtures.")
    ] = None,
    salida: Annotated[Path, typer.Option("--salida", help="Carpeta de salida.")] = Path(
        "out/esquemas"
    ),
) -> None:
    """Escribe propuestas de esquemas sin consultar bases de datos."""
    if not desde_programa.is_file():
        raise typer.BadParameter(f"no existe: {desde_programa}")
    catalogo = (Path.cwd() / "env" / "schemas").resolve()
    if salida.resolve() == catalogo or catalogo in salida.resolve().parents:
        raise typer.BadParameter("la propuesta no puede escribirse en env/schemas")
    fichas = {}
    if fixtures:
        for path in sorted(fixtures.rglob("*.ficha.yaml")):
            ficha = yaml.safe_load(path.read_text(encoding="utf-8"))
            fichas[ficha["tabla"].lower()] = [
                Column(name, tipo, None, "fixture") for name, tipo in ficha["columnas"].items()
            ]
    schemas, _ = esquemas_desde_programa(
        desde_programa.read_text(encoding="utf-8", errors="replace"), desde_programa.stem, fichas
    )
    salida.mkdir(parents=True, exist_ok=True)
    for tabla, columnas in schemas.items():
        sin_tipo = sum(c.source == "unknown" or c.type is None for c in columnas)
        typer.echo(f"{tabla}: {len(columnas)} columnas, {sin_tipo} sin tipo demostrado")
    for biblioteca, datos in a_json(schemas, desde_programa.name).items():
        (salida / f"{biblioteca}.json").write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
