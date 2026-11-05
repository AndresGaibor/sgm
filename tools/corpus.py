"""CLI del corpus de equivalencia SAS-Talend.

Uso (desde la raíz del repo):
    uv run python tools/corpus.py oraculo L1              calcula el esperado de un nivel (capa A)
    uv run python tools/corpus.py oraculo todos --verificar
                                                          compara lo calculado con lo guardado
    uv run python tools/corpus.py informe                 tabla Markdown de casos por nivel

Plan: docs/plan-reescritura/plan-corpus-y-equivalencia.md (secciones 3 y 6).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from corpus_lib.caso import resolver
from corpus_lib.informe import generar_informe
from corpus_lib.oraculo import ejecutar

REPO = Path(__file__).resolve().parents[1]
CORPUS_DEFECTO = REPO / "tests" / "corpus"


def _oraculo(args: argparse.Namespace) -> int:
    casos = resolver(args.corpus, args.objetivo)
    fallos = 0
    for caso in casos:
        resultado = ejecutar(caso, args.verificar)
        print(f"{resultado.estado.upper():10} {resultado.caso} (capa {caso.capa})")
        for linea in resultado.lineas:
            print(f"    {linea}")
        if not resultado.ok:
            fallos += 1
    print(f"{len(casos)} casos, {fallos} con falla")
    return 1 if fallos else 0


def _informe(args: argparse.Namespace) -> int:
    texto = generar_informe(args.corpus)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto, encoding="utf-8")
        print(f"informe escrito en {args.salida}")
    else:
        sys.stdout.write(texto)
    return 0


def main(argv: list[str] | None = None) -> int:
    # Windows usa la codificación de la consola por defecto; el corpus tiene tildes y Ñ.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Corpus de equivalencia SAS-Talend.")
    subcomandos = parser.add_subparsers(dest="orden", required=True)

    oraculo = subcomandos.add_parser("oraculo", help="calcula o verifica esperado/")
    oraculo.add_argument("objetivo", help="nombre de un caso, un nivel (L0...L9) o 'todos'")
    oraculo.add_argument(
        "--verificar",
        action="store_true",
        help="no escribe; compara lo calculado con lo guardado y falla si no coincide",
    )
    oraculo.add_argument("--corpus", type=Path, default=CORPUS_DEFECTO, help="carpeta del corpus")
    oraculo.set_defaults(func=_oraculo)

    informe = subcomandos.add_parser("informe", help="tabla Markdown de casos por nivel")
    informe.add_argument("--corpus", type=Path, default=CORPUS_DEFECTO, help="carpeta del corpus")
    informe.add_argument("--salida", type=Path, default=None, help="archivo donde escribirlo")
    informe.set_defaults(func=_informe)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
