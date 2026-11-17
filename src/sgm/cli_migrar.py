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

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

import typer

from sgm.backend_talend import ArchivosBackend, BackendTalend, TalendCliBackend
from sgm.catalog.config import Env, load_env
from sgm.catalog.schemas import load_schemas
from sgm.cli_migrar_contexto import _SECRETO as _SECRETO
from sgm.cli_migrar_contexto import _contexto_yaml
from sgm.cli_migrar_fuente import _FECHA_SIN_ARCHIVO as _FECHA_SIN_ARCHIVO
from sgm.cli_migrar_fuente import _fecha, _nombre
from sgm.compile import ROOT_DIR, compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.bibliotecas import cargar_decisiones_libnames
from sgm.ir.desplegar import plan_desplegado
from sgm.ir.models import Column, Plan
from sgm.migrar import informes
from sgm.migrar.esquemas import PendienteMigracion
from sgm.migrar.preparar_plan import esquemas_con_locales, preparar_plan
from sgm.migrar.tablas_locales import cargar_tablas_locales, raiz_repositorio
from sgm.seguridad.compuerta_migracion import publicar_con_revision
from sgm.seguridad.escaner_secretos import Hallazgo
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_conexion import cargar_contexto_dev
from sgm.talend_item.desde_plan_conexiones import conexiones_de_plan
from sgm.talend_item.desde_plan_contextos import GRUPOS, contextos_de_plan
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
    # Cambios de diseño del optimizador (`sgm.optimizar.Decision`).
    decisiones: list = field(default_factory=list)
    hallazgos_seguridad: tuple[Hallazgo, ...] = ()
    fallo_seguridad: str | None = None


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


def _lee_biblioteca(texto: str, nombre: str) -> bool:
    """Si el texto usa `NOMBRE.` como tabla: sin letra antes y sin distinguir mayúsculas."""
    mayus = texto.upper()
    marca = nombre.upper() + "."
    pos = mayus.find(marca)
    while pos != -1:
        if pos == 0 or not (mayus[pos - 1].isalnum() or mayus[pos - 1] == "_"):
            return True
        pos = mayus.find(marca, pos + 1)
    return False


def _base_del_programa(texto: str, decididas: set[str]) -> dict:
    """Base de compilación del programa. Solo usa `push_to_db` si lee una biblioteca declarada en
    `env/engines.json` (hoy `LZ`): el resto del corpus conserva la ubicación por flujo."""
    env = load_env()
    libs = {n: m for n, m in env.engines.library_engines().items() if n not in decididas}
    if any(_lee_biblioteca(texto, nombre) for nombre in libs):
        motores = replace(
            env.engines,
            libraries={n: m for n, m in env.engines.libraries.items() if n not in decididas},
        )
        env = Env(
            engines=motores,
            project=replace(env.project, placement_strategy="push_to_db"),
            externals=env.externals,
            external_files=env.external_files,
        )
        return project_base(env=env)
    return project_base(library_engines=libs)


def _plan(
    texto: str,
    nombre: str,
    resultado: ResultadoMigrar,
    decisiones_libnames: dict[str, dict] | None = None,
    analysis_items: list | None = None,
) -> Plan | None:
    """Plan del programa. Una excepción del análisis no tumba la migración: queda anotada."""
    try:
        analysis = analyze_program({f"{nombre}.sas": texto})
        if analysis_items is not None:
            analysis_items.extend(analysis.items)
        return compile_file(
            analysis,
            f"{nombre}.sas",
            _base_del_programa(texto, {n.upper() for n in (decisiones_libnames or {})}),
            libname_decisions=decisiones_libnames,
        ).plan
    except Exception as error:  # noqa: BLE001 — el comando no falla nunca; la causa va al log
        resultado.pendientes.append(
            PendienteMigracion(
                FALLO, f"no se pudo analizar el programa: {type(error).__name__}: {error}", None
            )
        )
        resultado.notas.append(f"{FALLO} análisis: {type(error).__name__}: {error}")
        return None


def _validar(resultado: ResultadoMigrar) -> None:
    """Convierte cada defecto estructural en un pendiente y en una nota del log.

    Un Job con defectos **no se escribe**: Studio lo abre con «Error al cargar el trabajo» y el
    usuario ve el fallo en la ventana, no en el informe. Queda el pendiente con su motivo.
    """
    aceptados = []
    for job in resultado.jobs:
        defectos = validar_job(job)
        for defecto in defectos:
            resultado.pendientes.append(
                PendienteMigracion(JOB_INVALIDO, f"{job.nombre}: {defecto}", None)
            )
            resultado.notas.append(f"{JOB_INVALIDO} {job.nombre}: {defecto}")
        if not defectos:
            aceptados.append(job)
    resultado.jobs = aceptados


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


def validate_backend(nombre: str) -> None:
    """Valida el backend antes de crear salidas, también en lotes de programas."""
    if nombre == "archivos":
        return
    if nombre == "talend":
        if not os.environ.get("SGM_TALEND_DIR") or not os.environ.get("SGM_TALEND_PROJECT"):
            raise typer.BadParameter(
                "--backend talend exige SGM_TALEND_DIR y SGM_TALEND_PROJECT en el entorno"
            )
        return
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
        informes.decisiones_tomadas_md(nombre, resultado.jobs, contextos, resultado.decisiones),
    )
    informes.escribir(
        carpeta, "trace.json", informes.trace_json(nombre, resultado.jobs, resultado.traza)
    )
    informes.escribir(
        carpeta,
        "cobertura.md",
        informes.cobertura_md(nombre, resultado.jobs, resultado.traza, resultado.pendientes),
    )
    informes.escribir(carpeta, "migracion.log", informes.migracion_log(resultado.notas))


def migrar(
    source: Path,
    out: Path,
    esquemas: Path | None = None,
    muestra: Path | None = None,
    backend: str = "archivos",
    tablas_locales: Path | None = None,
    contexto_dev: Path | None = None,
    libnames_decision: Path | None = None,
) -> ResultadoMigrar:
    """Migra un programa a `<out>/<programa>/`. No lanza: lo que falla queda en los informes."""
    locales = cargar_tablas_locales(tablas_locales, raiz_repositorio()) if tablas_locales else {}
    dev = cargar_contexto_dev(contexto_dev) if contexto_dev is not None else None
    resultado = ResultadoMigrar(out / _nombre(source))
    texto = _leer(source, resultado)
    decision_path = libnames_decision
    if decision_path is None:
        candidata = ROOT_DIR / "decisiones" / f"{source.stem}.libnames.yaml"
        decision_path = candidata if candidata.is_file() else None
    try:
        decisiones_libnames = cargar_decisiones_libnames(decision_path)
    except (OSError, ValueError) as error:
        decisiones_libnames = {}
        resultado.pendientes.append(
            PendienteMigracion(
                "P-LIBNAME-DECISION-INVALIDA",
                f"no se pudo leer la decisión de libnames: {error}",
                None,
            )
        )
    analysis_items: list = []
    plan = (
        _plan(texto, resultado.carpeta.name, resultado, decisiones_libnames, analysis_items)
        if texto is not None
        else None
    )
    contextos: dict[str, list[ParametroContexto]] = {}
    if plan is not None:
        # Las plantillas se escriben en línea: los esquemas y las rutas salen del plan desplegado.
        original = {op.id for op in plan.graph.operators()}
        plan, desplegados = plan_desplegado(plan)
        plan, previos = preparar_plan(plan, locales, texto=texto, items=analysis_items)
        resultado.pendientes += previos
        contextos = contextos_de_plan(plan, dev=dev)
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
        tablas, de_esquema = esquemas_con_locales(plan, _catalogo(esquemas), muestra, locales)
        resultado.pendientes += de_esquema
        usa_contexto_conexion = dev is not None or bool(conexiones_de_plan(plan))
        migracion = (
            plan_a_jobs(plan, tablas, conexion_en_contexto=True)
            if usa_contexto_conexion
            else plan_a_jobs(plan, tablas)
        )
        resultado.jobs = migracion.jobs
        resultado.pendientes += migracion.pendientes
        resultado.traza = migracion.traza
        # Se informa por los operadores del plan original: el `iterate` cuenta como visitado.
        resultado.visitados = (migracion.visitados & original) | desplegados
        resultado.plegados = migracion.plegados
        resultado.decisiones = migracion.decisiones
        _validar(resultado)
    carpeta_final = resultado.carpeta
    carpeta_candidata: Path | None = None

    def generar(carpeta: Path) -> None:
        nonlocal carpeta_candidata
        carpeta_candidata = carpeta
        resultado.carpeta = carpeta
        _escribir(resultado, contextos, backend, source)

    compuerta = publicar_con_revision(carpeta_final, generar)
    resultado.carpeta = carpeta_final
    if compuerta.publicado and carpeta_candidata is not None:
        resultado.escritos = [
            carpeta_final / ruta.relative_to(carpeta_candidata) for ruta in resultado.escritos
        ]
    else:
        resultado.escritos.clear()
        resultado.hallazgos_seguridad = compuerta.hallazgos
        resultado.fallo_seguridad = compuerta.motivo
    return resultado


def __getattr__(name: str):
    """Mantiene el comando importable desde su módulo original sin acoplar ambos módulos."""
    if name == "migrar_command":
        from sgm.cli_migrar_comando import migrar_command

        return migrar_command
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ResultadoMigrar", "migrar", "migrar_command"]  # noqa: F822
