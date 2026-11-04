"""Comando `sgm proceso`: escribe el documento de diseño deducido de un programa SAS.

Usa el modelo de proceso (linaje, familias de regiones, fuentes y salidas) y las decisiones del
equipo en `decisiones/<programa>.agrupacion.yaml` y `decisiones/<programa>.diseno.yaml`.
Va aparte de `sgm.cli` para no pasar el límite de 300 líneas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm.compile import ROOT_DIR
from sgm.proceso.diseno_doc import construir_documento
from sgm.proceso.render_md import render_markdown

DECISIONES = ROOT_DIR / "decisiones"


def _decision(ruta: Path | None, programa: Path, sufijo: str) -> Path:
    candidata = ruta or DECISIONES / f"{programa.stem}.{sufijo}.yaml"
    if not candidata.exists():
        raise typer.BadParameter(f"no existe: {candidata}")
    return candidata


def proceso_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas del programa.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    agrupacion: Annotated[
        Path | None, typer.Option("--agrupacion", help="YAML con marcador de región y productos.")
    ] = None,
    diseno: Annotated[
        Path | None, typer.Option("--diseno", help="YAML con etapas, fuentes y salidas.")
    ] = None,
) -> None:
    """Escribe `<programa>.diseno.md`: fuentes, salidas, equivalencias y pendientes."""
    if not source.is_file():
        raise typer.BadParameter(f"no es un archivo: {source}")
    doc = construir_documento(
        source, _decision(agrupacion, source, "agrupacion"), _decision(diseno, source, "diseno")
    )
    out.mkdir(parents=True, exist_ok=True)
    destino = out / f"{source.stem}.diseno.md"
    destino.write_text(render_markdown(doc), encoding="utf-8")
    typer.echo(f"{destino}: {len(doc.pendientes)} pendientes, {doc.resumen['familias']} familias.")
