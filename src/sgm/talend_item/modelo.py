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


@dataclass(frozen=True)
class Metadata:
    """Bloque `<metadata>` de un nodo: un conector (FLOW, REJECT, ...) con sus columnas."""

    conector: str
    nombre: str
    columnas: tuple[Columna, ...] = ()


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
    # Si se da, sustituye a `conector` y `columnas`: varios bloques `<metadata>` en orden.
    metadatas: list[Metadata] | None = None
    # XML de `<nodeData>` ya escrito (el mapeo de un tMap); vacío si el componente no lo tiene.
    datos: str = ""


@dataclass(frozen=True)
class Conexion:
    origen: str  # UNIQUE_NAME del nodo de origen
    destino: str
    nombre: str = "row1"
    conector: str = "FLOW"
    # lineStyle de Studio, verificado en Jobs reales: 0 fila, 1 OnSubjobOk, 3 OnComponentOk,
    # 6 Run if, 7 iterar, 13 paralelizar.
    estilo: int = 0
    # Parámetros propios de la conexión; si es None se escriben los de una fila.
    parametros: tuple[Fila, ...] | None = None
    etiqueta: str = ""  # texto de la línea; si está vacío se usa el nombre


@dataclass
class Job:
    nombre: str
    version: str = "0.1"
    nodos: list[Nodo] = field(default_factory=list)
    conexiones: list[Conexion] = field(default_factory=list)
