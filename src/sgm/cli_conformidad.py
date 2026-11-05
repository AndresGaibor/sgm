"""Comando `sgm conformidad`: cuánto del diseño manual sale del SAS, fila a fila.

Usa el mismo diseño que `sgm proceso` (`construir_documento`) y la referencia manual de
`tests/fixtures/referencia/diseno_manual.yaml`. La salida es determinista: el orden es el de la
referencia. Va aparte de `sgm.cli` para no pasar el límite de 300 líneas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm.cli_proceso import DECISIONES
from sgm.conformidad import informe
from sgm.conformidad.estado import clasificar_filas
from sgm.conformidad.referencia import cargar_secciones
from sgm.proceso.diseno_doc import SECCIONES_EMITIDAS, construir_documento

FORMATOS = ("texto", "json")


def _en_carpeta(carpeta: Path, programa: Path, sufijo: str) -> Path:
    candidata = carpeta / f"{programa.stem}.{sufijo}.yaml"
    if not candidata.exists():
        raise typer.BadParameter(f"no existe: {candidata}")
    return candidata


def conformidad_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas del programa.")],
    decisiones: Annotated[
        Path | None,
        typer.Option("--decisiones", help="Carpeta con los YAML de decisiones (decisiones/)."),
    ] = None,
    formato: Annotated[str, typer.Option("--formato", help="texto o json.")] = "texto",
) -> None:
    """Resume el estado de cada fila del diseño manual: derivada, declarada, pendiente o diferente.

    Sale en texto o en JSON. Con las mismas entradas, la salida es idéntica entre corridas.
    """
    if not source.is_file():
        raise typer.BadParameter(f"no es un archivo: {source}")
    if formato not in FORMATOS:
        raise typer.BadParameter(f"formato desconocido {formato!r}; use texto o json")
    carpeta = decisiones or DECISIONES
    doc = construir_documento(
        source,
        _en_carpeta(carpeta, source, "agrupacion"),
        _en_carpeta(carpeta, source, "diseno"),
    )
    filas = clasificar_filas(
        cargar_secciones(), doc.secciones, doc.origenes, SECCIONES_EMITIDAS
    )
    resumen = informe.resumir(filas)
    if formato == "json":
        typer.echo(informe.json_del_informe(source.name, resumen, filas))
    else:
        typer.echo(informe.texto(source.name, resumen))
