"""Comando `sgm migrar`: de un programa SAS a los Jobs de Talend, sin ningún YAML.

Es la primera rebanada vertical del migrador general: el programa entra, y lo que sale es una
carpeta que se puede abrir en Studio y leer:

    <out>/<programa>/process/<job>_<versión>.item   el Job
    <out>/<programa>/contextos/<grupo>.yaml         los valores de cada entorno
    <out>/<programa>/pendientes.md                  lo que no se pudo traducir, con su línea
    <out>/<programa>/configuracion-pendiente.md     lo que hay que completar antes de ejecutar
    <out>/<programa>/decisiones-tomadas.md          qué eligió el migrador y cómo cambiarlo
    <out>/<programa>/trace.json                     qué líneas del SAS originaron cada nodo
    <out>/<programa>/migracion.log                  la causa técnica de cada fallo interno

La promesa del comando es **no fallar nunca**: un operador que no se sabe traducir queda en
`pendientes.md`, un defecto estructural del Job se escribe igual con su `P-JOB-INVALIDO`, un
backend que se rompe no se lleva los informes, y un archivo que no es SAS sale con código 0 y su
explicación. El código de salida 2 queda para el uso incorrecto de la línea de comandos: una ruta
que no existe o un `--backend` que no existe.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from sgm.backend_talend import ArchivosBackend, BackendTalend, TalendCliBackend
from sgm.catalog.schemas import load_schemas
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column, Plan
from sgm.migrar import informes
from sgm.migrar.esquemas import PendienteMigracion, esquemas_de_entrada
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_contextos import GRUPOS, contextos_de_plan
from sgm.talend_item.escritura import fecha_studio
from sgm.talend_item.modelo import Job, ParametroContexto
from sgm.talend_item.validador import validar_job

# Un programa que no llegó a ningún paso: vacío, o con sentencias que el analizador no reconoció.
SIN_PASOS = "P-SIN-PASOS"
# Un Job que el validador estructural rechaza. Se escribe igual: la persona lo abre y lo ve.
JOB_INVALIDO = "P-JOB-INVALIDO"
# El backend falló al escribir un Job. Los informes se escriben de todos modos.
FALLO_ESCRITURA = "P-FALLO-ESCRITURA"
# El archivo no se pudo leer del disco.
ILLEGIBLE = "P-PROGRAMA-ILLEGIBLE"
# Una excepción no prevista durante el análisis o la compilación.
FALLO = "P-FALLO-INTERNO"
# Un nombre de variable que huele a credencial no se escribe con su valor, ni en el YAML.
_SECRETO = re.compile(r"(pass|pwd|secret|token|clave)", re.IGNORECASE)


@dataclass
class ResultadoMigrar:
    """Lo que dejó una migración: la carpeta, los Jobs, lo pendiente y las notas técnicas."""

    carpeta: Path
    jobs: list[Job] = field(default_factory=list)
    pendientes: list[PendienteMigracion] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)
    traza: dict[str, list[int]] = field(default_factory=dict)
    # Operadores del plan que se recorrieron: uno que falte no dejó nodo ni pendiente.
    visitados: set[str] = field(default_factory=set)
    # `read`/`write` que solo nombran un flujo ya producido: no son pasos, se pliegan.
    plegados: set[str] = field(default_factory=set)
    escritos: list[Path] = field(default_factory=list)


def _nombre(source: Path) -> str:
    """Nombre de la carpeta de salida: el del programa, sin extensión."""
    return source.stem or source.name


def _fecha(source: Path) -> str:
    """Fecha de modificación del programa en el formato de los `.properties`.

    No es la del reloj a propósito: con la fecha del archivo, dos corridas sobre el mismo programa
    dan los mismos bytes y dos migraciones se pueden comparar con `diff`.
    """
    try:
        marca = source.stat().st_mtime
    except OSError:
        marca = 0.0
    return fecha_studio(datetime.fromtimestamp(marca).astimezone())


def _catalogo(esquemas: Path | None) -> dict[str, list[Column]]:
    """Esquemas de `--esquemas`, indexados también por el nombre de tabla sin su esquema.

    Los archivos de `env/schemas/` llevan las tablas como `<esquema>.<tabla>`, y el SAS las nombra
    `WORK.<tabla>`: sin este segundo índice el catálogo nunca se encontraría. Si dos esquemas traen
    la misma tabla, gana la primera clave en orden alfabético; para evitarlo, nombra la tabla con su
    esquema en el programa.
    """
    if esquemas is None:
        return {}
    cargados = load_schemas(esquemas)
    catalogo = dict(cargados)
    for clave, columnas in sorted(cargados.items()):
        catalogo.setdefault(clave.split(".")[-1], columnas)
    return catalogo


def _leer(source: Path, resultado: ResultadoMigrar) -> str | None:
    """Texto del programa, o `None` con el pendiente puesto si no se puede leer."""
    try:
        return source.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        resultado.pendientes.append(
            PendienteMigracion(ILLEGIBLE, f"{source.name}: no se pudo leer ({error})", None)
        )
        resultado.notas.append(f"{ILLEGIBLE} {source.name}: {type(error).__name__}: {error}")
        return None


def _plan(texto: str, nombre: str, resultado: ResultadoMigrar) -> Plan | None:
    """Plan del programa. Una excepción del análisis no tumba la migración: queda anotada."""
    try:
        analysis = analyze_program({f"{nombre}.sas": texto})
        return compile_file(analysis, f"{nombre}.sas", project_base()).plan
    except Exception as error:  # noqa: BLE001 — el comando no falla nunca; la causa va al log
        resultado.pendientes.append(
            PendienteMigracion(
                FALLO, f"no se pudo analizar el programa: {type(error).__name__}: {error}", None
            )
        )
        resultado.notas.append(f"{FALLO} análisis: {type(error).__name__}: {error}")
        return None


def _validar(resultado: ResultadoMigrar) -> None:
    """Convierte cada defecto estructural en un pendiente y en una nota del log."""
    for job in resultado.jobs:
        for defecto in validar_job(job):
            resultado.pendientes.append(
                PendienteMigracion(JOB_INVALIDO, f"{job.nombre}: {defecto}", None)
            )
            resultado.notas.append(f"{JOB_INVALIDO} {job.nombre}: {defecto}")


def _contexto_yaml(grupo: str, parametros: list[ParametroContexto]) -> str:
    """Un grupo de contexto como YAML: la lista de variables, con su valor y para qué sirve."""
    lineas = [
        f"# Contexto {grupo} del Job.",
        "# Editar estos valores y volver a importar el Job: el .item no se toca.",
        f"grupo: {grupo}",
    ]
    if not parametros:
        return "\n".join([*lineas, "variables: []", ""])
    lineas.append("variables:")
    for parametro in parametros:
        oculto = bool(_SECRETO.search(parametro.nombre))
        descripcion = parametro.comentario or "sin descripción"
        if oculto:
            descripcion += " (valor oculto: no se escribe en el archivo)"
        lineas += [
            f"  - nombre: {parametro.nombre}",
            f"    tipo: {parametro.tipo}",
            f"    valor: {json.dumps('' if oculto else parametro.valor, ensure_ascii=False)}",
            f"    descripcion: {json.dumps(descripcion, ensure_ascii=False)}",
        ]
    return "\n".join([*lineas, ""])


def _backend(nombre: str, fecha: str) -> BackendTalend:
    """Backend de escritura. Un nombre desconocido es uso incorrecto de la línea de comandos."""
    if nombre == "archivos":
        return ArchivosBackend(fecha=fecha)
    if nombre == "talend":
        carpeta = os.environ.get("SGM_TALEND_DIR")
        proyecto = os.environ.get("SGM_TALEND_PROJECT")
        if not carpeta or not proyecto:
            raise typer.BadParameter(
                "--backend talend exige SGM_TALEND_DIR y SGM_TALEND_PROJECT en el entorno"
            )
        return TalendCliBackend(Path(carpeta), Path(proyecto), fecha=fecha)
    raise typer.BadParameter(f"backend desconocido: {nombre} (usa 'archivos' o 'talend')")


def _escribir(
    resultado: ResultadoMigrar,
    contextos: dict[str, list[ParametroContexto]],
    backend: str,
    source: Path,
) -> None:
    """Escribe los Jobs y los cinco documentos. Ningún fallo deja la carpeta a medias."""
    nombre = resultado.carpeta.name
    carpeta = resultado.carpeta
    carpeta.mkdir(parents=True, exist_ok=True)
    escritor = _backend(backend, _fecha(source))
    for job in resultado.jobs:
        try:
            resultado.escritos += escritor.escribir([job], carpeta / "process")
        except Exception as error:  # noqa: BLE001 — un Job que no se escribe no se lleva el resto
            resultado.pendientes.append(
                PendienteMigracion(FALLO_ESCRITURA, f"{job.nombre}: {error}", None)
            )
            resultado.notas.append(
                f"{FALLO_ESCRITURA} {job.nombre}: {type(error).__name__}: {error}"
            )
    for grupo in GRUPOS:
        informes.escribir(
            carpeta / "contextos", f"{grupo}.yaml", _contexto_yaml(grupo, contextos.get(grupo, []))
        )
    informes.escribir(
        carpeta, "pendientes.md", informes.pendientes_md(nombre, resultado.pendientes)
    )
    informes.escribir(
        carpeta,
        "configuracion-pendiente.md",
        informes.configuracion_pendiente_md(nombre, contextos, resultado.jobs),
    )
    informes.escribir(
        carpeta,
        "decisiones-tomadas.md",
        informes.decisiones_tomadas_md(nombre, resultado.jobs, contextos),
    )
    informes.escribir(
        carpeta, "trace.json", informes.trace_json(nombre, resultado.jobs, resultado.traza)
    )
    informes.escribir(carpeta, "migracion.log", informes.migracion_log(resultado.notas))


def migrar(
    source: Path,
    out: Path,
    esquemas: Path | None = None,
    muestra: Path | None = None,
    backend: str = "archivos",
) -> ResultadoMigrar:
    """Migra un programa a `<out>/<programa>/`. No lanza: lo que falla queda en los informes."""
    resultado = ResultadoMigrar(out / _nombre(source))
    texto = _leer(source, resultado)
    plan = _plan(texto, resultado.carpeta.name, resultado) if texto is not None else None
    contextos: dict[str, list[ParametroContexto]] = {}
    if plan is not None:
        contextos = contextos_de_plan(plan)
        if not len(plan.graph):
            resultado.pendientes.append(
                PendienteMigracion(
                    SIN_PASOS,
                    "el programa no tiene ningún paso que migrar: puede estar vacío, o sus "
                    "sentencias no se reconocieron (%macro sin %mend, %include de un archivo que "
                    "no está)",
                    None,
                )
            )
        tablas, de_esquema = esquemas_de_entrada(plan, _catalogo(esquemas), muestra)
        resultado.pendientes += de_esquema
        migracion = plan_a_jobs(plan, tablas)
        resultado.jobs = migracion.jobs
        resultado.pendientes += migracion.pendientes
        resultado.traza = migracion.traza
        resultado.visitados = migracion.visitados
        resultado.plegados = migracion.plegados
        _validar(resultado)
    _escribir(resultado, contextos, backend, source)
    return resultado


def migrar_command(
    source: Annotated[Path, typer.Argument(help="Programa SAS a migrar.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
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
    """Migra un programa SAS a Jobs de Talend: `process/`, contextos y los informes."""
    if not source.is_file():
        raise typer.BadParameter(f"no existe el programa: {source}")
    if esquemas is not None and not esquemas.is_dir():
        raise typer.BadParameter(f"no existe la carpeta de esquemas: {esquemas}")
    if muestra is not None and not muestra.is_dir():
        raise typer.BadParameter(f"no existe la carpeta de muestra: {muestra}")
    resultado = migrar(source, out, esquemas=esquemas, muestra=muestra, backend=backend)
    typer.echo(
        f"{source.name}: {len(resultado.jobs)} Job(s), {len(resultado.pendientes)} pendiente(s), "
        f"salida en {resultado.carpeta}"
    )
    if resultado.pendientes:
        typer.echo(f"  ver {resultado.carpeta / 'pendientes.md'}")


__all__ = ["ResultadoMigrar", "migrar", "migrar_command"]
