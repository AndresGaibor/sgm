"""Genera las entradas CSV de los casos L2 y L3 con datos ficticios y semilla fija.

Es reproducible: dos ejecuciones dan los mismos bytes. Desde la carpeta `tools/`:

    uv run python -m corpus_lib.generar_entradas_l2l3

Escribe en `tests/corpus/<nivel>/<caso>/entradas/`. Si el caso declara `preparacion` en su
`caso.yaml`, escribe también `entradas_preparadas/` con el resultado del DATA step. Los datos son
inventados y evidentes como tales.
"""

from __future__ import annotations

from pathlib import Path

from .caso import cargar_caso
from .datos_ficticios import Entrada, escribir_entrada, generar_tabla
from .especificaciones_l2 import ESPECIFICACIONES_L2
from .especificaciones_l3 import ESPECIFICACIONES_L3
from .esquemas_l2l3 import Fija
from .preparacion import generar as generar_preparada

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "tests" / "corpus"
ESPECIFICACIONES = {**ESPECIFICACIONES_L2, **ESPECIFICACIONES_L3}


def generar_todo(corpus: Path = CORPUS) -> list[Path]:
    """Escribe las entradas de todos los casos L2 y L3 y devuelve los archivos escritos.

    La carpeta de cada caso debe tener su `caso.yaml`, porque la preparación se lee de ahí.
    """
    escritos: list[Path] = []
    for caso, tablas in sorted(ESPECIFICACIONES.items()):
        nivel = caso.split("_", 1)[0].upper()
        carpeta = corpus / nivel / caso
        for nombre, especificacion in tablas.items():
            encabezado, filas = _tabla(caso, nombre, especificacion)
            escribir_entrada(carpeta / "entradas", nombre, encabezado, filas)
            escritos.append(carpeta / "entradas" / f"{nombre}.csv")
        preparada = _preparar(carpeta)
        if preparada is not None:
            escritos.append(preparada)
    return escritos


def _tabla(caso: str, nombre: str, especificacion: Entrada | Fija) -> tuple[list[str], list]:
    if isinstance(especificacion, Fija):
        return list(especificacion.encabezado), [list(fila) for fila in especificacion.filas]
    return generar_tabla(f"{caso}:{nombre}", especificacion)


def _preparar(carpeta: Path) -> Path | None:
    caso = cargar_caso(carpeta)
    if caso.preparacion is None:
        return None
    caso.entradas_preparadas.mkdir(parents=True, exist_ok=True)
    return generar_preparada(caso.entradas, caso.entradas_preparadas, caso.preparacion)


def main() -> int:
    escritos = generar_todo()
    print(f"{len(escritos)} archivos de entrada escritos en {CORPUS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
