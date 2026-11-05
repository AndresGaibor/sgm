"""Genera las entradas CSV de los casos L0 y L1 con datos ficticios y semilla fija.

Es reproducible: dos ejecuciones dan los mismos bytes. Desde la carpeta `tools/`:

    uv run python -m corpus_lib.generar_entradas

Escribe en `tests/corpus/<nivel>/<caso>/entradas/`. Los datos son inventados y evidentes como tales.
"""

from __future__ import annotations

from pathlib import Path

from .datos_ficticios import escribir_entrada, generar_tabla
from .especificaciones_l0 import ESPECIFICACIONES_L0
from .especificaciones_l1 import ESPECIFICACIONES_L1

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "tests" / "corpus"
ESPECIFICACIONES = {**ESPECIFICACIONES_L0, **ESPECIFICACIONES_L1}


def generar_todo(corpus: Path = CORPUS) -> list[Path]:
    """Escribe todas las entradas y devuelve la lista de archivos escritos."""
    escritos: list[Path] = []
    for caso, archivos in sorted(ESPECIFICACIONES.items()):
        nivel = caso.split("_", 1)[0].upper()
        carpeta = corpus / nivel / caso / "entradas"
        for nombre, entrada in archivos.items():
            encabezado, filas = generar_tabla(f"{caso}:{nombre}", entrada)
            escribir_entrada(carpeta, nombre, encabezado, filas)
            escritos.append(carpeta / f"{nombre}.csv")
    return escritos


def main() -> int:
    escritos = generar_todo()
    print(f"{len(escritos)} archivos de entrada escritos en {CORPUS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
