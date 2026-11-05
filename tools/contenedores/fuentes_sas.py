"""Extrae del programa SAS las tablas base que lee y las columnas que usa de cada una.

Reutiliza el análisis de `sgm` (flujo y columnas usadas). Solo considera fuentes con nombre
literal `biblioteca.tabla`: los nombres dinámicos (macrovariables) quedan fuera y se reportan.
"""

from dataclasses import dataclass
from pathlib import Path

from sgm.flow.model import build_flows
from sgm.proceso.columnas_fuente import columnas_usadas
from sgm.proceso.entradas_salidas import entradas_y_salidas


@dataclass(frozen=True)
class TablaBase:
    """Tabla que el programa lee de una biblioteca (base de datos en Impala)."""

    biblioteca: str  # en minúsculas: Impala no distingue mayúsculas
    tabla: str
    columnas: tuple[str, ...]


@dataclass(frozen=True)
class Omitida:
    """Fuente que no se puede crear sin más información, con su motivo."""

    nombre: str
    motivo: str


def _nombre_literal(ubicacion: str) -> bool:
    partes = ubicacion.split(".")
    return len(partes) == 2 and all(p.isidentifier() for p in partes)


def tablas_base(ruta_sas: Path) -> tuple[list[TablaBase], list[Omitida]]:
    """Devuelve las tablas base del programa y las fuentes omitidas con su motivo."""
    texto = ruta_sas.read_text(encoding="utf-8", errors="replace")
    vistas: dict[str, TablaBase] = {}
    omitidas: list[Omitida] = []
    for modelo in build_flows({str(ruta_sas): texto}).values():
        for fuente in entradas_y_salidas(modelo, {}).fuentes:
            if fuente.tipo != "tabla_base":
                continue
            nombre = fuente.ubicacion
            clave = nombre.lower()
            if clave in vistas:
                continue
            if not _nombre_literal(nombre):
                omitidas.append(Omitida(nombre, "nombre no literal biblioteca.tabla"))
                continue
            columnas = tuple(columnas_usadas(texto, nombre))
            if not columnas:
                omitidas.append(Omitida(nombre, "el programa no usa columnas identificables"))
                continue
            biblioteca, tabla = clave.split(".")
            vistas[clave] = TablaBase(biblioteca, tabla, columnas)
    return list(vistas.values()), omitidas
