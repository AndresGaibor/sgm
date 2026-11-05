"""Escribe los archivos de datos de producto simulados que el programa SAS lee.

Uso: uv run python tools/simular_productos.py <programa.sas> <carpeta_salida> [--filas N]
     [--saldo COLUMNA]

Por cada producto escribe su archivo principal (ver `proceso/origen_producto.py`) con el delimitador
y la anchura que el SAS demuestra, sin cabecera, y N filas (5 por defecto) de datos evidentemente
falsos: `SIM_<columna>_<n>`. Sirve para probar los Jobs de Talend sin los datos reales.

Con `--saldo COLUMNA`, esa columna se escribe como número con punto decimal (`100.50 * n`) para que
la suma de saldo del Job tenga algo que sumar; el resto de columnas sigue como texto.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sgm.agrupacion import cargar_declaracion
from sgm.compile import ROOT_DIR
from sgm.proceso.origen_producto import origenes_producto


def _valor(nombre: str, i: int, saldo: str | None) -> str:
    """Valor simulado de una celda: número con punto para la columna de saldo, texto si no."""
    if saldo is not None and nombre == saldo:
        return f"{100.5 * i:.2f}"
    return f"SIM_{nombre}_{i}"


def simular(
    programa: Path,
    salida: Path,
    filas: int,
    agrupacion: Path | None = None,
    saldo: str | None = None,
) -> list[Path]:
    texto = programa.read_text(encoding="utf-8", errors="replace")
    ruta = agrupacion or ROOT_DIR / "decisiones" / f"{programa.stem}.agrupacion.yaml"
    origenes = origenes_producto(texto, cargar_declaracion(ruta).productos)
    salida.mkdir(parents=True, exist_ok=True)
    escritos = []
    for origen in origenes.por_producto.values():
        nombres = origenes.columnas_comunes
        lineas = [
            origen.fuente.delimitador.join(_valor(c, i, saldo) for c in nombres)
            for i in range(1, filas + 1)
        ]
        destino = salida / origen.fuente.archivo
        destino.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
        escritos.append(destino)
    return escritos


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("programa", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--filas", type=int, default=5)
    parser.add_argument("--saldo", default=None, metavar="COLUMNA")
    args = parser.parse_args(argv)
    for destino in simular(args.programa, args.salida, args.filas, saldo=args.saldo):
        print(f"{destino.name}: {args.filas} filas simuladas")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
