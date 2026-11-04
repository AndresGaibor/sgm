"""Fase 0 del plan de reescritura: mide tres hipótesis sobre un programa SAS (sin construir nada).

Uso: uv run python tools/medir_fase0.py [programa.sas] [--agrupacion yaml] [--out json]

- H1 fontanería: fracción de operadores que son fontanería según las reglas existentes.
- H2 tablas WORK: ciclo de vida de los conjuntos de datos (fuentes, aristas, salidas).
- H3 similitud entre regiones: LCS de tipos de operador sin fontanería.

Los sufijos de producto salen del YAML de decisiones; el script no lleva nombres del programa.
Escribe un JSON determinista (sin fechas) y no modifica nada de `src/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fase0 import h1, h2, h3  # noqa: E402
from fase0.captura import capturar  # noqa: E402

from sgm.agrupacion import cargar_declaracion, inicios_de  # noqa: E402
from sgm.generador import marcador_de_regiones  # noqa: E402

PROGRAMA = ROOT / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
SALIDA = ROOT / "docs" / "plan-reescritura" / "fase0-mediciones.json"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("programa", nargs="?", type=Path, default=PROGRAMA)
    ap.add_argument("--agrupacion", type=Path, default=None)
    ap.add_argument("--diseno", type=Path, default=None, help="Diseño manual para comparar H2.")
    ap.add_argument("--out", type=Path, default=SALIDA)
    args = ap.parse_args(argv)

    yaml_decisiones = (
        args.agrupacion or ROOT / "decisiones" / f"{args.programa.stem}.agrupacion.yaml"
    )
    decl = cargar_declaracion(yaml_decisiones) if yaml_decisiones.exists() else None
    diseno = args.diseno
    if diseno is None:
        candidatos = sorted((ROOT / "docs").glob("diseno-talend-*.md"))
        diseno = candidatos[0] if candidatos else None

    c = capturar(args.programa)
    inicios = inicios_de(c.lineas, decl.marcador) if decl else marcador_de_regiones(c.lineas)
    resultado = {
        "metadatos": {
            "programa": args.programa.name,
            "lineas": len(c.lineas),
            "regiones": len(inicios),
            "marcador_de_region": decl.marcador if decl else "macro más repetida (sin YAML)",
            "agrupacion": yaml_decisiones.name if decl else None,
            "diseno_manual": diseno.name if diseno else None,
        },
        "h1_fontaneria": h1.medir(c),
        "h2_tablas": h2.medir(c.hechos, inicios, decl, diseno, c.texto),
        "h3_similitud": h3.medir(c, inicios, decl),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Escrito {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
