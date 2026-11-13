"""Espacio de combinaciones de `OUTPUT` que genera el corpus (B-17).

Cada combinación es una estructura de ramas (`IF`, `IF/ELSE`, `IF/ELSE IF`, `IF/ELSE IF/ELSE`,
sin `IF`) con un `OUTPUT` por rama, y cada `OUTPUT` nombra 0, 1 o 2 de los tres datasets del
encabezado `DATA` (0 = todos). Las ramas de una cadena son excluyentes, así que pueden repetir
destino. Las ramas de `IF` independientes no pueden repetirlo: `OUTPUT_DESTINO_REPETIDO` lo rechaza,
y el generador no lo produce (son casos negativos, aparte).

Fuera de este espacio por ahora: el `OUTPUT` seguido de una continuación del paso y la captura
del PDV entre dos `OUTPUT`. Quedan como parte pendiente de B-17.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import product

DATASETS = ("S1", "S2", "S3")
# Condición de cada bloque: (variable, operador, constante). `None` es el ELSE.
CONDICION_1 = ("VALOR", "<=", 2)
CONDICION_2 = ("VALOR", ">=", 4)
DESTINOS = ((), ("S1",), ("S1", "S2"))  # omitido (todos), uno, dos

# Ramas: por bloque, la condición (o None para el ELSE final), y si la rama es cadena (excluyente).
ESTRUCTURAS: dict[str, tuple[tuple[tuple | None, ...], bool]] = {
    "incondicional": ((None,), False),
    "if": ((CONDICION_1,), False),
    "if_else": ((CONDICION_1, None), True),
    "if_elseif": ((CONDICION_1, CONDICION_2), True),
    "if_elseif_else": ((CONDICION_1, CONDICION_2, None), True),
}


@dataclass(frozen=True)
class Combinacion:
    """Una estructura de ramas con el destino de cada `OUTPUT`."""

    rama: str
    destinos: tuple[tuple[str, ...], ...]

    @property
    def condiciones(self) -> tuple[tuple | None, ...]:
        return ESTRUCTURAS[self.rama][0]

    @property
    def nombre(self) -> str:
        partes = ["-".join(d) if d else "todos" for d in self.destinos]
        return f"{self.rama}__" + "__".join(partes)

    def programa_sas(self) -> str:
        """El programa completo: entrada, el `DATA` con sus ramas y ninguna sentencia más."""
        cabecera = " ".join(f"WORK.{d}" for d in DATASETS)
        lineas = [
            "PROC IMPORT DATAFILE='.../entradas/REGISTROS.csv' OUT=WORK.REGISTROS DBMS=CSV "
            "REPLACE;",
            "    GETNAMES=YES;",
            "RUN;",
            "",
            f"DATA {cabecera};",
            "    SET WORK.REGISTROS;",
        ]
        bloques = [self._bloque(i) for i in range(len(self.destinos))]
        if self.rama == "incondicional":
            lineas.append(f"    {bloques[0]}")
        else:
            cadena = ESTRUCTURAS[self.rama][1]
            for i, (condicion, sentencia) in enumerate(zip(self.condiciones, bloques, strict=True)):
                if condicion is None:
                    lineas.append(f"    ELSE {sentencia}")
                    continue
                prefijo = "ELSE IF" if cadena and i > 0 else "IF"
                lineas.append(f"    {prefijo} {_texto(condicion)} THEN {sentencia}")
        lineas.append("RUN;")
        return "\n".join(lineas) + "\n"

    def _bloque(self, i: int) -> str:
        destinos = self.destinos[i]
        return "OUTPUT " + " ".join(f"WORK.{d}" for d in destinos) + ";" if destinos else "OUTPUT;"


def _texto(condicion: tuple) -> str:
    variable, operador, constante = condicion
    return f"{variable} {operador} {constante}"


def combinaciones() -> Iterator[Combinacion]:
    """Todas las combinaciones del espacio, en orden estable."""
    for rama, (condiciones, cadena) in ESTRUCTURAS.items():
        for destinos in product(DESTINOS, repeat=len(condiciones)):
            if not cadena and _repite_destino(destinos):
                continue  # ramas independientes: un destino repetido es un caso negativo
            yield Combinacion(rama, tuple(destinos))


def _repite_destino(destinos: tuple[tuple[str, ...], ...]) -> bool:
    """Si dos bloques independientes escriben al mismo dataset (o uno escribe a todos)."""
    if any(not d for d in destinos) and len(destinos) > 1:
        return True
    vistos: set[str] = set()
    for d in destinos:
        if vistos & set(d):
            return True
        vistos |= set(d)
    return False
