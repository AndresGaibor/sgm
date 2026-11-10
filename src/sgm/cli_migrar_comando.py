"""Interfaz de `sgm migrar` para programas individuales y carpetas."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm.cli_migrar import migrar, validate_backend


def _seguridad_fallida(resultado) -> bool:
    return bool(resultado.hallazgos_seguridad or resultado.fallo_seguridad)


def _informar_seguridad(resultado) -> None:
    for hallazgo in resultado.hallazgos_seguridad:
        typer.echo(
            f"  seguridad: {hallazgo.archivo}:{hallazgo.linea}: {hallazgo.tipo}; "
            "valor oculto, paquete no publicado"
        )
    if resultado.fallo_seguridad:
        typer.echo(f"  seguridad: {resultado.fallo_seguridad}; paquete no publicado")


def _sas_programs(source_dir: Path, output_dir: Path) -> list[Path]:
    """Lista archivos SAS en orden estable, sin volver a leer una salida anidada."""
    source_root = source_dir.resolve()
    output_root = output_dir.resolve()
    try:
        output_relative = output_root.relative_to(source_root).parts
    except ValueError:
        output_relative = ()
    exclude_output = bool(output_relative)

    programs = [
        path
        for path in source_dir.rglob("*")
        if path.is_file()
        and path.suffix.casefold() == ".sas"
        and not (exclude_output and path.resolve().is_relative_to(output_root))
    ]
    return sorted(
        programs,
        key=lambda path: (
            path.relative_to(source_dir).as_posix().casefold(),
            path.relative_to(source_dir).as_posix(),
        ),
    )


def migrar_command(
    source: Annotated[Path, typer.Argument(help="Programa SAS o carpeta de programas SAS.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta base de salida.")] = Path("out"),
    esquemas: Annotated[
        Path | None,
        typer.Option("--esquemas", help="Carpeta de esquemas del entorno, como la de env/schemas."),
    ] = None,
    muestra: Annotated[
        Path | None,
        typer.Option("--muestra", help="Carpeta con archivos de muestra de las entradas."),
    ] = None,
    backend: Annotated[
        str, typer.Option("--backend", help="'archivos' (por omisión) o 'talend'.")
    ] = "archivos",
) -> None:
    """Migra un SAS o cada `.sas` de una carpeta, con un paquete separado por programa."""
    if not source.is_file() and not source.is_dir():
        raise typer.BadParameter(f"no existe el programa o la carpeta: {source}")
    if esquemas is not None and not esquemas.is_dir():
        raise typer.BadParameter(f"no existe la carpeta de esquemas: {esquemas}")
    if muestra is not None and not muestra.is_dir():
        raise typer.BadParameter(f"no existe la carpeta de muestra: {muestra}")
    validate_backend(backend)

    if source.is_file():
        resultado = migrar(source, out, esquemas=esquemas, muestra=muestra, backend=backend)
        salida = (
            "paquete no publicado por seguridad"
            if _seguridad_fallida(resultado)
            else f"salida en {resultado.carpeta}"
        )
        typer.echo(
            f"{source.name}: {len(resultado.jobs)} Job(s), "
            f"{len(resultado.pendientes)} pendiente(s), "
            f"{salida}"
        )
        if _seguridad_fallida(resultado):
            _informar_seguridad(resultado)
            raise typer.Exit(code=1)
        if resultado.pendientes:
            typer.echo(f"  ver {resultado.carpeta / 'pendientes.md'}")
        return

    programs = _sas_programs(source, out)
    if not programs:
        typer.echo(f"No hay programas SAS (.sas) en {source}.")
        return

    results = [
        migrar(
            program,
            out / program.relative_to(source).parent,
            esquemas=esquemas,
            muestra=muestra,
            backend=backend,
        )
        for program in programs
    ]
    job_count = sum(len(result.jobs) for result in results)
    pending_count = sum(len(result.pendientes) for result in results)
    typer.echo(
        f"{len(results)} programa(s), {job_count} Job(s), "
        f"{pending_count} pendiente(s). Informes por programa en {out}."
    )
    typer.echo("Recorrido por ruta relativa; el orden no representa dependencias de ejecución.")
    bloqueados = [resultado for resultado in results if _seguridad_fallida(resultado)]
    if bloqueados:
        typer.echo(f"Compuerta de seguridad: {len(bloqueados)} paquete(s) no publicado(s).")
        for resultado in bloqueados:
            _informar_seguridad(resultado)
    programs_with_pending = sum(bool(result.pendientes) for result in results)
    if programs_with_pending:
        typer.echo(
            f"Revise pendientes.md y cobertura.md en las salidas de "
            f"{programs_with_pending} programa(s)."
        )
    if bloqueados:
        raise typer.Exit(code=1)


__all__ = ["migrar_command"]
