"""Cobertura de etapas declaradas sobre las etiquetas de un programa SAS. Solo lee. Uso:

    uv run python tools/cobertura_etapas.py --sas P.sas --agrupacion A.yaml --diseno D.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sgm.agrupacion import cargar_declaracion
from sgm.flow.regiones import dividir_regiones
from sgm.proceso.etapas import cargar_etapas, cobertura


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sas", type=Path, required=True)
    parser.add_argument("--agrupacion", type=Path, required=True)
    parser.add_argument("--diseno", type=Path, required=True)
    parser.add_argument("--sueltas", type=int, default=40, help="etiquetas sin etapa a listar")
    args = parser.parse_args()

    texto = args.sas.read_text(encoding="utf-8", errors="replace")
    regiones = dividir_regiones(texto, cargar_declaracion(args.agrupacion).marcador)
    etiquetas = [e for r in regiones for e in r.etiquetas]
    res = cobertura(etiquetas, cargar_etapas(args.diseno))
    print(f"{res.total} etiquetas, {res.porcentaje_cubierto:.1f} % con etapa")
    for nombre, n in res.por_etapa.most_common():
        print(f"  {nombre:<28}{n:>5}")
    unicas = sorted(set(res.sin_etapa))
    print(f"sin etapa: {len(res.sin_etapa)} ({len(unicas)} distintas)")
    for e in unicas[: args.sueltas]:
        print("   -", e)


if __name__ == "__main__":
    main()
