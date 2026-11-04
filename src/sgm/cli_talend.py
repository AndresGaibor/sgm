"""Comando `sgm talend`: escribe los Jobs de Talend (`.item` y `.properties`) de un programa SAS.

Parte de la arquitectura declarada en `decisiones/<programa>.jobs.yaml` y de los productos de
`decisiones/<programa>.agrupacion.yaml`. Los datos que el SAS no demuestra quedan vacíos y se
listan como pendientes. Va aparte de `sgm.cli` para no pasar el límite de 300 líneas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm.agrupacion import cargar_declaracion
from sgm.cli_proceso import _decision
from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.escritura import escribir_job
from sgm.talend_item.jobs_diseno import ProductoJob, job_padre, jobs_hijos


def talend_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas del programa.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    agrupacion: Annotated[
        Path | None, typer.Option("--agrupacion", help="YAML con marcador de región y productos.")
    ] = None,
    jobs_yaml: Annotated[
        Path | None, typer.Option("--jobs", help="YAML con la arquitectura de Jobs.")
    ] = None,
) -> None:
    """Escribe en `<out>/<programa>/talend/process/` los Jobs del diseño."""
    if not source.is_file():
        raise typer.BadParameter(f"no es un archivo: {source}")
    declaracion = cargar_declaracion(_decision(agrupacion, source, "agrupacion"))
    arq = cargar_arquitectura(_decision(jobs_yaml, source, "jobs"))
    productos = [ProductoJob(p, "", p) for p in declaracion.productos]
    destino = out / source.stem / "talend" / "process"
    jobs = [job_padre(arq, productos), *jobs_hijos(arq)]
    escritos = [escribir_job(job, destino) for job in jobs]
    for item, _ in escritos:
        typer.echo(str(item))
    typer.echo(f"{len(escritos)} Jobs escritos.")
    typer.echo(f"Pendiente: tabla de origen de {len(productos)} productos (no está en el SAS).")
