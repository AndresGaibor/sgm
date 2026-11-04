"""Insumos de archivo de un programa: qué ruta, qué variables de contexto y qué columnas.

Une lo que el equipo declaró (`fuentes` de `decisiones/<programa>.diseno.yaml`: la clave, la
expresión `busca` y la ubicación `variable_ruta + variable_archivo`) con lo que el SAS demuestra:
la ruta del `PROC IMPORT` y las columnas que el programa usa de ese archivo. Lo que no se halla o
no se demuestra queda en `pendientes` con su motivo; nada se completa por suposición.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sgm.proceso.columnas_fuente import columnas_por_importacion
from sgm.proceso.entradas_salidas import nombre_archivo

_UBICACION = re.compile(r"^\s*(\w+)\s*\+\s*(\w+)\s*$")


@dataclass(frozen=True)
class InsumoResuelto:
    fuente: str  # clave de la tabla 1.1
    ruta: str  # ruta completa del archivo, tal como la escribe el SAS
    directorio: str  # la ruta sin el nombre del archivo (con su separador final)
    archivo: str
    variable_ruta: str  # variable de contexto del directorio
    variable_archivo: str  # variable de contexto del nombre de archivo
    columnas: tuple[str, ...]  # las que el SAS usa; vacío = esquema pendiente


@dataclass
class InsumosResueltos:
    insumos: dict[str, InsumoResuelto] = field(default_factory=dict)
    pendientes: list[str] = field(default_factory=list)


def resolver_insumos(
    texto: str, declaradas: list[dict[str, str]], claves: list[str]
) -> InsumosResueltos:
    """Resuelve cada fuente de `claves` contra los `PROC IMPORT` del programa."""
    columnas = columnas_por_importacion(texto)
    por_clave = {d["clave"]: d for d in declaradas}
    resultado = InsumosResueltos()
    for clave in claves:
        declarada = por_clave.get(clave)
        if declarada is None:
            resultado.pendientes.append(f"{clave}: no está declarada en las fuentes del diseño")
            continue
        ubicacion = _UBICACION.match(declarada.get("ubicacion", ""))
        if not ubicacion or not declarada.get("busca"):
            resultado.pendientes.append(f"{clave}: la ubicación no es `variable + variable`")
            continue
        patron = re.compile(declarada["busca"], re.IGNORECASE)
        ruta = next((r for r in columnas if patron.search(r)), None)
        if ruta is None:
            resultado.pendientes.append(f"{clave}: el SAS no importa ningún archivo que la case")
            continue
        archivo = nombre_archivo(ruta)
        if not columnas[ruta]:
            resultado.pendientes.append(f"{clave}: el SAS no usa ninguna columna de {archivo}")
        resultado.insumos[clave] = InsumoResuelto(
            clave,
            ruta,
            ruta[: len(ruta) - len(archivo)],
            archivo,
            ubicacion.group(1),
            ubicacion.group(2),
            tuple(columnas[ruta]),
        )
    directorios = {i.directorio for i in resultado.insumos.values()}
    if len(directorios) > 1:
        resultado.pendientes.append(f"los insumos están en {len(directorios)} carpetas distintas")
    return resultado
