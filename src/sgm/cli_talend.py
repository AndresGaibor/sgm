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
from sgm.proceso.insumos import InsumosResueltos, resolver_insumos
from sgm.proceso.secciones_entrada import cargar_declaradas
from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.escritura import escribir_job
from sgm.talend_item.jobs_diseno import ProductoJob, job_padre, jobs_hijos
from sgm.talend_item.periodo import contextos_de_periodo, nodos_periodo


def _descripcion_lookups(arq, resueltos: InsumosResueltos) -> str:
    """Los Excel que `job_producto` usará como lookup, con las columnas que el SAS les usa."""
    partes = []
    for clave in arq.lookups:
        insumo = resueltos.insumos.get(clave)
        if insumo:
            partes.append(f"{insumo.archivo} ({', '.join(insumo.columnas) or 'sin columnas'})")
    return f". Lookups: {'; '.join(partes)}" if partes else ""


def talend_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas del programa.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    agrupacion: Annotated[
        Path | None, typer.Option("--agrupacion", help="YAML con marcador de región y productos.")
    ] = None,
    jobs_yaml: Annotated[
        Path | None, typer.Option("--jobs", help="YAML con la arquitectura de Jobs.")
    ] = None,
    diseno: Annotated[
        Path | None, typer.Option("--diseno", help="YAML con las fuentes declaradas.")
    ] = None,
) -> None:
    """Escribe en `<out>/<programa>/talend/process/` los Jobs del diseño."""
    if not source.is_file():
        raise typer.BadParameter(f"no es un archivo: {source}")
    declaracion = cargar_declaracion(_decision(agrupacion, source, "agrupacion"))
    arq = cargar_arquitectura(_decision(jobs_yaml, source, "jobs"))
    productos = [ProductoJob(p, "", p) for p in declaracion.productos]
    texto = source.read_text(encoding="utf-8", errors="replace")
    declaradas = cargar_declaradas(_decision(diseno, source, "diseno"), "fuentes")
    claves = [*arq.lookups, *([arq.periodo.fuente] if arq.periodo else [])]
    resueltos = resolver_insumos(texto, declaradas, claves)
    padre = job_padre(
        arq,
        productos,
        periodo=nodos_periodo(arq, resueltos),
        contextos_periodo=contextos_de_periodo(arq, resueltos),
    )
    variables = tuple(v for _, v in arq.periodo.variables) if arq.periodo else ()
    jobs = [padre, *jobs_hijos(arq, variables, _descripcion_lookups(arq, resueltos))]
    destino = out / source.stem / "talend" / "process"
    escritos = [escribir_job(job, destino) for job in jobs]
    for item, _ in escritos:
        typer.echo(str(item))
    typer.echo(f"{len(escritos)} Jobs escritos.")
    typer.echo(f"Pendiente: tabla de origen de {len(productos)} productos (no está en el SAS).")
    for pendiente in resueltos.pendientes:
        typer.echo(f"Pendiente: {pendiente}")
