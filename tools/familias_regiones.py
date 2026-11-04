"""Familias de regiones de un programa SAS: copias por producto y regiones sin copia.

Solo lee. El marcador de región y los productos salen del YAML de agrupación. Uso:

    uv run python tools/familias_regiones.py --sas RUTA.sas --agrupacion RUTA.agrupacion.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sgm.agrupacion import cargar_declaracion
from sgm.flow.regiones import dividir_regiones
from sgm.proceso.familias import (
    UMBRAL_FAMILIA,
    detectar_familias,
    normalizar_region,
    producto_de_texto,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sas", type=Path, required=True)
    parser.add_argument("--agrupacion", type=Path, required=True)
    parser.add_argument("--umbral", type=float, default=UMBRAL_FAMILIA)
    args = parser.parse_args()

    texto = args.sas.read_text(encoding="utf-8", errors="replace")
    decl = cargar_declaracion(args.agrupacion)
    regiones = dividir_regiones(texto, decl.marcador)
    lineas_sas = texto.split("\n")
    sufijos = [s for suf in decl.productos.values() for s in suf]
    textos = {r.indice: "\n".join(lineas_sas[r.linea_inicio - 1 : r.linea_fin]) for r in regiones}
    normal = {i: normalizar_region(t, sufijos) for i, t in textos.items()}
    producto = {i: producto_de_texto(t, decl.productos) for i, t in textos.items()}
    res = detectar_familias(normal, producto, args.umbral)
    print(f"{len(regiones)} regiones; umbral {args.umbral}")
    for fam in res.familias:
        miembros = ", ".join(f"{i.region}:{i.producto or '?'}" for i in fam.instancias)
        rep = f" REPETIDOS {fam.productos_repetidos}" if fam.productos_repetidos else ""
        print(
            f"familia {fam.id:>2}: {fam.lineas:>5} líneas, min {fam.similitud_minima:.3f} "
            f"[{miembros}]{rep}"
        )
    print(
        "sin copia:", ", ".join(f"{i}:{producto[i] or '?'}({len(normal[i])})" for i in res.unicas)
    )


if __name__ == "__main__":
    main()
