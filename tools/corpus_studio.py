"""Arnés de Studio del corpus: ejecuta Jobs de Talend con las entradas de un caso y compara.

Uso (desde la raíz del repo):
    uv run python tools/corpus_studio.py validar <caso> --jobs CARPETA --padre NOMBRE \
        --proyecto RUTA [--contexto clave=valor ...] [--mapa mapa.yaml]
    uv run python tools/corpus_studio.py comparar <caso> --salida CARPETA
    uv run python tools/corpus_studio.py lote <caso...> --jobs CARPETA --proyecto RUTA
    uv run python tools/corpus_studio.py pendientes

`validar` necesita el servidor talend-mcp arrancado con escritura y ejecución (ver
`tools/validar_en_studio.py`). `comparar` no usa Studio y es lo que va a pytest. `lote` compila
muchos Jobs en una sola llamada, con un sufijo nuevo y limpiando `process/` al terminar. Si Studio
no está disponible, `validar` y `lote` dejan sus casos en `out/studio-pendientes.json` y
`pendientes` vuelve a intentarlos; un pendiente nunca se cuenta como validado.
Documentación: tools/corpus_lib/STUDIO.md. Plan: docs/plan-reescritura/plan-corpus-y-equivalencia.md
(sección 6).

Código de salida: 0 solo si todos los archivos del caso coinciden; 1 si hay diferencias o un
error de Studio; 2 si el uso o un archivo no son válidos.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from corpus_lib.caso import resolver
from corpus_lib.studio_cola import (
    MOTIVO_REINTENTO,
    RUTA_POR_OMISION,
    Pendiente,
    encolar,
    leer,
    vaciar,
)
from corpus_lib.studio_informe import ResultadoCaso, comparar_caso, tabla_markdown
from corpus_lib.studio_lote import compilar_en_lote
from corpus_lib.studio_mapa import leer_mapa
from corpus_lib.studio_validar import sufijo_nuevo, validar_en_studio
from mcp_cliente import ErrorValidacion

from sgm.backend_talend import McpBackend, TalendCliBackend
from sgm.backend_talend.salud import comprobar_salud

REPO = Path(__file__).resolve().parents[1]
CORPUS_DEFECTO = REPO / "tests" / "corpus"


def _un_caso(corpus: Path, objetivo: str):
    casos = resolver(corpus, objetivo)
    if len(casos) != 1:
        raise ValueError(f"se necesita un caso, no {len(casos)} casos de '{objetivo}'")
    return casos[0]


def _emitir(resultado: ResultadoCaso, ruta: Path | None) -> int:
    texto = tabla_markdown([resultado])
    if ruta:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")
        print(f"informe escrito en {ruta}")
    sys.stdout.write(texto)
    return 0 if resultado.coincide else 1


def _comparar(args: argparse.Namespace) -> int:
    caso = _un_caso(args.corpus, args.caso)
    if not args.salida.is_dir():
        raise ValueError(f"no existe la carpeta de salida: {args.salida}")
    resultado = comparar_caso(
        caso, args.salida, ignorar_orden_columnas=args.ignorar_orden_columnas
    )
    return _emitir(resultado, args.informe)


def _validar(args: argparse.Namespace) -> int:
    caso = _un_caso(args.corpus, args.caso)
    salud = comprobar_salud(McpBackend(tiempo_max=args.tiempo_max))
    if not salud.ok:
        encolar(args.cola, Pendiente(caso.nombre, salud.estado or "SIN_ESTADO"))
        print(f"Studio no está disponible ({salud.estado}): {salud.motivo}")
        print(f"el caso {caso.nombre} quedó en la cola {args.cola}")
        return 1
    if not args.proyecto:
        raise ValueError("falta --proyecto (o la variable TALEND_PROJECT)")
    mapa = leer_mapa(args.mapa)
    ejecucion = validar_en_studio(
        caso,
        args.jobs,
        args.padre,
        args.proyecto,
        parametros=args.contexto,
        mapa=mapa,
        trabajo=args.trabajo,
        sufijo=args.sufijo,
        contexto=args.grupo_contexto,
        java_bin=args.java_bin,
        m2=args.m2,
    )
    print(f"Carpeta de trabajo: {ejecucion.trabajo}")
    print(f"Salida: {[p.name for p in ejecucion.salida] or 'ninguna'}")
    if ejecucion.stderr:
        print(f"stderr (final): {ejecucion.stderr[-800:]}")
    resultado = comparar_caso(
        caso,
        ejecucion.trabajo / "salida",
        error=ejecucion.error,
        ignorar_orden_columnas=args.ignorar_orden_columnas,
    )
    return _emitir(resultado, args.informe)


def _lote(args: argparse.Namespace) -> int:
    """Compila los Jobs de los casos dados en una sola llamada a Studio."""
    if not args.proyecto:
        raise ValueError("falta --proyecto (o la variable TALEND_PROJECT)")
    if not args.jobs.is_dir():
        raise ValueError(f"no existe la carpeta de Jobs: {args.jobs}")
    carpetas = []
    for caso in args.casos:
        propia = args.jobs / caso
        carpetas.append(propia if propia.is_dir() else args.jobs)
    if args.backend == "mcp":
        backend = McpBackend(url=args.url, tiempo_max=args.tiempo_max)
    else:
        backend = TalendCliBackend(args.talend_dir, args.proyecto, tiempo_max=args.tiempo_max)
    salud = comprobar_salud(backend)
    if not salud.ok:
        for caso in args.casos:
            encolar(args.cola, Pendiente(caso, salud.estado or "SIN_ESTADO"))
        print(f"Studio no está disponible ({salud.estado}): {salud.motivo}")
        print(f"{len(args.casos)} casos quedaron en la cola {args.cola}")
        return 1
    sufijo = args.sufijo or sufijo_nuevo()
    inicio = time.perf_counter()
    resultado = compilar_en_lote(carpetas, args.proyecto, backend, sufijo)
    segundos = time.perf_counter() - inicio
    print(
        f"Lote de {len(carpetas)} Jobs (sufijo {sufijo}) en {segundos:.1f} s: "
        f"{len(resultado.compilan)} compilan, {len(resultado.no_compilan)} no"
    )
    for nombre, motivo in sorted(resultado.no_compilan.items()):
        print(f"  no compila {nombre}: {motivo}")
    return 0 if not resultado.no_compilan else 1


def _pendientes(args: argparse.Namespace) -> int:
    """Reintenta la cola con Studio sano y quita lo que se resuelva."""
    pendientes = leer(args.cola)
    if not pendientes:
        print(f"No hay validaciones pendientes en {args.cola}.")
        return 0
    validador = Path(__file__).resolve().parent / "validar_caso_studio.py"
    resueltos: set[str] = set()
    fallidos: list[str] = []
    for pendiente in pendientes:
        print(f"reintentando {pendiente.caso} (intento {pendiente.intentos + 1})")
        codigo = subprocess.call([sys.executable, str(validador), pendiente.caso], cwd=str(REPO))
        if codigo == 0:
            resueltos.add(pendiente.caso)
        else:
            fallidos.append(pendiente.caso)
    vaciar(args.cola, resueltos)
    for caso in fallidos:
        encolar(args.cola, Pendiente(caso, MOTIVO_REINTENTO))
    siguen = len(leer(args.cola))
    print(f"{len(resueltos)} resueltos, {siguen} siguen pendientes")
    return 0 if siguen == 0 else 1


def _agregar_cola(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cola", type=Path, default=RUTA_POR_OMISION, help="cola de pendientes")


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Arnés de Studio del corpus SAS-Talend.")
    subcomandos = parser.add_subparsers(dest="orden", required=True)

    validar = subcomandos.add_parser("validar", help="ejecuta los Jobs en Studio y compara")
    validar.add_argument("caso", help="nombre del caso del corpus")
    validar.add_argument("--jobs", type=Path, required=True, help="carpeta con .item y .properties")
    validar.add_argument("--padre", required=True, help="nombre del Job que se ejecuta")
    validar.add_argument(
        "--proyecto",
        type=Path,
        default=os.environ.get("TALEND_PROJECT"),
        help="carpeta del proyecto Talend (con talend.project); por defecto TALEND_PROJECT",
    )
    validar.add_argument(
        "--contexto", action="append", default=[], metavar="CLAVE=VALOR",
        help="variable de contexto literal; se puede repetir",
    )
    validar.add_argument("--mapa", type=Path, help="mapa.yaml: variable -> ruta del caso")
    validar.add_argument("--grupo-contexto", default="Default", help="grupo de contexto del Job")
    validar.add_argument("--trabajo", type=Path, help="carpeta de trabajo (por defecto temporal)")
    validar.add_argument("--sufijo", help="sufijo nuevo de los Jobs (por defecto, con fecha)")
    validar.add_argument("--java-bin", type=Path, help="carpeta bin del JDK de Studio")
    validar.add_argument("--m2", type=Path, help="caché .m2 de Studio para descargar poms")
    validar.add_argument("--informe", type=Path, help="escribe el informe Markdown en este archivo")
    validar.add_argument("--ignorar-orden-columnas", action="store_true")
    validar.add_argument("--corpus", type=Path, default=CORPUS_DEFECTO)
    validar.add_argument("--tiempo-max", type=float, default=10.0, help="segundos por llamada")
    _agregar_cola(validar)
    validar.set_defaults(func=_validar)

    comparar = subcomandos.add_parser("comparar", help="compara una carpeta de salida ya hecha")
    comparar.add_argument("caso", help="nombre del caso del corpus")
    comparar.add_argument("--salida", type=Path, required=True, help="carpeta con los CSV")
    comparar.add_argument("--informe", type=Path, help="escribe el informe Markdown")
    comparar.add_argument("--ignorar-orden-columnas", action="store_true")
    comparar.add_argument("--corpus", type=Path, default=CORPUS_DEFECTO)
    comparar.set_defaults(func=_comparar)

    lote = subcomandos.add_parser("lote", help="compila varios Jobs en una sola llamada")
    lote.add_argument("casos", nargs="+", help="casos del corpus cuyos Jobs se compilan")
    lote.add_argument(
        "--jobs",
        type=Path,
        required=True,
        help="carpeta con los Jobs, o con una subcarpeta por caso",
    )
    lote.add_argument(
        "--proyecto",
        type=Path,
        default=os.environ.get("TALEND_PROJECT"),
        help="carpeta del proyecto Talend (con talend.project); por defecto TALEND_PROJECT",
    )
    lote.add_argument(
        "--backend", choices=["talend_cli", "mcp"], default="talend_cli", help="backend de Talend"
    )
    lote.add_argument(
        "--url",
        default=None,
        help="URL del MCP; por defecto TALEND_MCP_URL o http://127.0.0.1:3927/mcp",
    )
    lote.add_argument(
        "--talend-dir",
        type=Path,
        default=os.environ.get("TALEND_MCP_DIR"),
        help="carpeta de talend-mcp; por defecto TALEND_MCP_DIR",
    )
    lote.add_argument("--sufijo", help="sufijo nuevo de los Jobs (por defecto, con fecha)")
    lote.add_argument("--tiempo-max", type=float, default=900.0, help="segundos por llamada")
    _agregar_cola(lote)
    lote.set_defaults(func=_lote)

    pendientes = subcomandos.add_parser(
        "pendientes", help="reintenta lo que quedó en la cola de validaciones"
    )
    _agregar_cola(pendientes)
    pendientes.set_defaults(func=_pendientes)
    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows usa la codificación de la consola por defecto; el corpus tiene tildes y Ñ.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    args = _crear_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError, ErrorValidacion) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
