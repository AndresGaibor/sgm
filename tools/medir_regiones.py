"""Cuenta los pasos del flujo por región, con la regla nueva y con la de línea de evidencia.

Solo lee: no escribe archivos. El marcador sale de `--marcador` o, si no se pasa, del campo
`region_marcador` del YAML de agrupación (`--agrupacion`). Uso:

    uv run python tools/medir_regiones.py --sas RUTA.sas --agrupacion RUTA.agrupacion.yaml
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from sgm.agrupacion import cargar_declaracion
from sgm.flow.model import build_flows
from sgm.flow.regiones import asignar_regiones, dividir_regiones, region_de_linea


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sas", type=Path, required=True, help="programa SAS a medir")
    parser.add_argument("--agrupacion", type=Path, help="YAML con region_marcador")
    parser.add_argument("--marcador", help="marcador de región (sustituye al del YAML)")
    return parser


def _marcador(args: argparse.Namespace) -> str:
    if args.marcador:
        return args.marcador
    if args.agrupacion is None:
        raise SystemExit("falta --marcador o --agrupacion")
    return cargar_declaracion(args.agrupacion).marcador


def _imprimir(titulo: str, conteo: Counter, total: int, n_regiones: int) -> None:
    print(titulo)
    for indice in range(n_regiones):
        print(f"  region {indice:>3}: {conteo.get(indice, 0):>6}")
    con_pasos = sum(1 for indice in conteo if conteo[indice])
    print(f"  total: {total}, regiones con pasos: {con_pasos}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    marcador = _marcador(args)
    texto = args.sas.read_text(encoding="utf-8-sig")
    modelo = build_flows({args.sas.name: texto})[args.sas.name]
    regiones = dividir_regiones(texto, marcador)
    nuevo = Counter(asignar_regiones(modelo, regiones).values())
    # Regla de comparación: la región que contiene la línea de evidencia del paso.
    por_evidencia = Counter(region_de_linea(regiones, paso.line) for paso in modelo.steps)
    total = len(modelo.steps)
    print(f"marcador: {marcador!r}, regiones: {len(regiones)}")
    _imprimir("regla nueva (línea de la llamada de macro si la hay)", nuevo, total, len(regiones))
    _imprimir("regla de línea de evidencia", por_evidencia, total, len(regiones))
    return 0


if __name__ == "__main__":
    sys.exit(main())
