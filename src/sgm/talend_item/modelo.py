"""Modelo mínimo de un Job de Talend: nodos con parámetros, conexiones y subjobs.

Solo lo necesario para escribir el `.item`. Los componentes concretos viven en `componentes.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

Fila = tuple[str, str, str | None, str | None]  # (campo, nombre, valor, show)


@dataclass(frozen=True)
class Columna:
    nombre: str
    tipo: str = "id_String"  # tipo de Talend: id_String, id_Integer, id_Long, id_Date, ...
    nulable: bool = True
    clave: bool = False
    longitud: int = -1
    precision: int = -1
    patron: str = ""


@dataclass(frozen=True)
class Tabla:
    """Parámetro de tipo TABLE: una lista de (elementRef, valor)."""

    nombre: str
    celdas: tuple[tuple[str, str], ...]
    show: str | None = None


@dataclass
class Nodo:
    componente: str  # nombre del componente: tFixedFlowInput, tLogRow, ...
    version: str  # versión del componente tal como la guarda Studio: "0.102"
    unico: str  # UNIQUE_NAME: tFixedFlowInput_1
    x: int = 0
    y: int = 0
    parametros: list[Fila | Tabla] = field(default_factory=list)  # en el orden en que se escriben
    columnas: list[Columna] = field(default_factory=list)
    conector: str = "FLOW"


@dataclass(frozen=True)
class Conexion:
    origen: str  # UNIQUE_NAME del nodo de origen
    destino: str
    nombre: str = "row1"
    conector: str = "FLOW"
    estilo: int = (
        0  # 0 = fila, 1 = OnSubjobOk, 3 = OnComponentOk, 4 = OnSubjobError, 5 = OnComponentError
    )


@dataclass
class Job:
    nombre: str
    version: str = "0.1"
    nodos: list[Nodo] = field(default_factory=list)
    conexiones: list[Conexion] = field(default_factory=list)
