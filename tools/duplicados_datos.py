"""Hito 92 / R1-12: duplicados por llave (`PROC SORT NODUPKEY`) contra el Job emitido.

Oráculo en Python de la regla de `proceso/reglas_duplicados.py`: se conserva la primera fila de
cada llave en el orden de entrada (`EQUALS`). La comparación de llaves sigue la semántica de SAS:

* Blancos finales no cuentan: `'C3 '` es `'C3'`.
* Un texto solo con blancos es faltante, y el faltante es igual a `''`.
* Mayúsculas y minúsculas cuentan (la comparación de `BY` es sensible a mayúsculas).

Los vectores de `VECTORES` están clasificados a mano desde esa semántica, no con este oráculo; la
prueba comprueba que el oráculo los reproduce. El caso `L8/totales/01` aporta la prueba real: su
`AHO_UNICOS.csv` esperado sale de `origen_aho.csv` con la misma regla.

Uso desde `tools/prueba_duplicados.py`; no se importa desde `src/`.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "totales" / "01_duplicados_frecuencias"
COLUMNAS_VECTORES = ("CLAVE", "SALDO")
LLAVES_VECTORES = ("CLAVE",)


def recorte(texto: str | None) -> str:
    """Texto sin blancos finales; un nulo o solo con blancos da cadena vacía (faltante de SAS)."""
    return "" if texto is None else texto.rstrip(" ")


def llave(fila: dict[str, str], llaves: tuple[str, ...]) -> tuple[str, ...]:
    """Llave de comparación: cada `BY` recortado, sensible a mayúsculas."""
    return tuple(recorte(fila.get(c)) for c in llaves)


@dataclass
class Resultado:
    """Filas que sobreviven (primera de cada llave) y repetidas, en el orden de entrada."""

    unicas: list[dict[str, str]] = field(default_factory=list)
    repetidas: list[dict[str, str]] = field(default_factory=list)


def clasificar(filas: list[dict[str, str]], llaves: tuple[str, ...]) -> Resultado:
    """La primera fila de cada llave va a `unicas`; las siguientes, a `repetidas`."""
    vistas: set[tuple[str, ...]] = set()
    salida = Resultado()
    for fila in filas:
        clave = llave(fila, llaves)
        if clave in vistas:
            salida.repetidas.append(fila)
        else:
            vistas.add(clave)
            salida.unicas.append(fila)
    return salida


# Vectores a mano. Cada grupo usa llaves propias, para que los grupos no se mezclen al unirse en
# un solo archivo. `claves` son las llaves que sobreviven (ya recortadas), `repetidas` cuántas
# filas se descartan y `motivo` dice qué semántica ejerce el grupo.
VECTORES: tuple[tuple[str, list[tuple[str, str]], list[str], int, str], ...] = (
    (
        "duplicado_exacto",
        [("A1", "10"), ("A1", "10"), ("G7", "11")],
        ["A1", "G7"],
        1,
        "fila exacta",
    ),
    ("misma_llave_otro_saldo", [("B2", "30"), ("B2", "40")], ["B2"], 1, "conserva el 30"),
    ("blancos_finales", [("C3 ", "50"), ("C3", "60")], ["C3"], 1, "C3 con blancos es C3"),
    ("mayusculas", [("d4", "1"), ("D4", "2")], ["d4", "D4"], 0, "d4 y D4 son llaves distintas"),
    ("faltante", [("", "5"), ("   ", "6")], [""], 1, "blanco y vacío son el mismo faltante"),
    ("tres_repetidos", [("E5", "1"), ("E5", "2"), ("E5", "3")], ["E5"], 2, "conserva el 1"),
)


def vectores() -> list[dict[str, str]]:
    """Filas de `VECTORES` en el orden de entrada, con columnas `CLAVE` y `SALDO`."""
    return [
        {"CLAVE": clave, "SALDO": saldo}
        for _, pares, _, _, _ in VECTORES
        for clave, saldo in pares
    ]


def vector_csv(ruta: Path) -> Path:
    """Escribe los vectores como CSV con cabecera (delimitador `,`)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as salida:
        escritor = csv.writer(salida, lineterminator="\n")
        escritor.writerow(COLUMNAS_VECTORES)
        for fila in vectores():
            escritor.writerow([fila[c] for c in COLUMNAS_VECTORES])
    return ruta


def esperado_vectores() -> tuple[list[str], int]:
    """Llaves únicas esperadas (a mano, recortadas) y el número de filas repetidas."""
    unicas: list[str] = []
    repetidas = 0
    for _, _, claves, n, _ in VECTORES:
        unicas.extend(claves)
        repetidas += n
    return unicas, repetidas


def primera_de_cada_grupo() -> list[tuple[str, str]]:
    """Pareja (llave recortada, saldo) que debe sobrevivir: la primera fila de cada llave."""
    sobreviven: list[tuple[str, str]] = []
    for _, pares, _, _, _ in VECTORES:
        vistas: set[str] = set()
        for clave, saldo in pares:
            if recorte(clave) not in vistas:
                vistas.add(recorte(clave))
                sobreviven.append((recorte(clave), saldo))
    return sobreviven


def informe_vectores(unicas: list[dict[str, str]], repetidas: list[dict[str, str]]) -> list[str]:
    """Diferencias entre lo que sacó el Job (UNICOS y DUPLICADOS) y los vectores a mano.

    Compara la pareja (llave, saldo) de cada sobreviviente, así que una fila que no es la primera
    de su llave falla aunque la llave sea la correcta.
    """
    _, n_repetidas = esperado_vectores()
    errores: list[str] = []
    obtenidas = sorted((recorte(f["CLAVE"]), f["SALDO"]) for f in unicas)
    esperadas = sorted(primera_de_cada_grupo())
    if obtenidas != esperadas:
        errores.append(f"únicas: esperadas {esperadas}, obtenidas {obtenidas}")
    if len(repetidas) != n_repetidas:
        errores.append(f"repetidas: esperadas {n_repetidas}, obtenidas {len(repetidas)}")
    return errores


def leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8", newline="") as entrada:
        return list(csv.DictReader(entrada))


def caso_origen() -> Path:
    return CASO / "entradas" / "origen_aho.csv"


def caso_esperado(nombre: str) -> list[dict[str, str]]:
    return leer_csv(CASO / "esperado" / f"{nombre}.csv")


__all__ = [
    "COLUMNAS_VECTORES",
    "LLAVES_VECTORES",
    "VECTORES",
    "Resultado",
    "caso_esperado",
    "caso_origen",
    "clasificar",
    "esperado_vectores",
    "informe_vectores",
    "leer_csv",
    "primera_de_cada_grupo",
    "llave",
    "recorte",
    "vector_csv",
    "vectores",
]
