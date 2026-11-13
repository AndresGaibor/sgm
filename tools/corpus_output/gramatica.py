"""Espacio de combinaciones de `OUTPUT` que genera el corpus (B-17).

Cada combinación es una estructura de ramas (`IF`, `IF/ELSE`, `IF/ELSE IF`, `IF/ELSE IF/ELSE`,
sin `IF`) con un `OUTPUT` por rama, y cada `OUTPUT` nombra 0, 1 o 2 de los tres datasets del
encabezado `DATA` (0 = todos). Las ramas de una cadena son excluyentes, así que pueden repetir
destino. Las ramas de `IF` independientes no pueden repetirlo: `OUTPUT_DESTINO_REPETIDO` lo rechaza,
y el generador no lo produce (son casos negativos, aparte).

Cada combinación se da con y sin una asignación después de la cadena (continuación). Fuera del
espacio, por ahora: la captura del PDV entre dos `OUTPUT` (ver BLOQUEOS, B-17).
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
    # Dos IF sin cadena: un OUTPUT por cada uno. Con DESTINOS no hay ninguna combinación sin repetir
    # dataset, así que todas son negativos (`negativos()`).
    "dos_if_independientes": ((CONDICION_1, CONDICION_2), False),
}


@dataclass(frozen=True)
class Combinacion:
    """Una estructura de ramas con el destino de cada `OUTPUT`."""

    rama: str
    destinos: tuple[tuple[str, ...], ...]
    # Continuación: una asignación después de la cadena de `OUTPUT`. La fila ya se escribió, así que
    # no cambia lo que sale (`lrcon`, p. 498: el PDV se escribe al ejecutarse el `OUTPUT`).
    continuacion: bool = False

    @property
    def condiciones(self) -> tuple[tuple | None, ...]:
        return ESTRUCTURAS[self.rama][0]

    @property
    def nombre(self) -> str:
        partes = ["-".join(d) if d else "todos" for d in self.destinos]
        sufijo = "__cont" if self.continuacion else ""
        return f"{self.rama}__" + "__".join(partes) + sufijo

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
        if self.continuacion:
            lineas.append("    CONT = 1;")
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
            for continuacion in (False, True):
                yield Combinacion(rama, tuple(destinos), continuacion)


def negativos() -> Iterator[Combinacion]:
    """Combinaciones que el traductor no emite: ramas independientes que repiten destino. SAS las
    acepta (cada `OUTPUT` escribe el PDV como una observación, `lrcon` p. 498); el traductor no
    tiene operador de unión para ellas, así que quedan como pendiente y no como Job."""
    for rama, (condiciones, cadena) in ESTRUCTURAS.items():
        if cadena or len(condiciones) < 2:
            continue
        for destinos in product(DESTINOS, repeat=len(condiciones)):
            if _repite_destino(destinos):
                for continuacion in (False, True):
                    yield Combinacion(rama, tuple(destinos), continuacion)


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
