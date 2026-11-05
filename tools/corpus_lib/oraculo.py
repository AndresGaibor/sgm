"""Orquesta el oráculo de un caso: usa la capa declarada y escribe o verifica `esperado/`.

Capa A calcula con SQLite. Capa C no tiene oráculo ejecutable: su `esperado/` lo escribe una persona
o un agente y lo revisa otro. Capa B queda pendiente de los vectores de semántica (tarea K06).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .caso import Caso
from .csv_tabla import Tabla, comparar_con_guardado, escribir_csv, leer_entradas, ordenar_filas
from .oraculo_sql import ErrorSql, ejecutar_proc_sql
from .preparacion import verificar as verificar_preparacion
from .sas_texto import sentencias_proc_sql
from .traduccion_sql import NoSoportado


@dataclass
class Resultado:
    """Resultado del oráculo para un caso. `estado` es escrito, verificado, omitido o falla."""

    caso: str
    estado: str
    lineas: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.estado != "falla"


def _entradas_para_sql(caso: Caso) -> dict[str, Tabla]:
    """Entradas del PROC SQL. Con `preparacion`, son las del DATA step, tras comprobarlas."""
    if caso.preparacion is None:
        return leer_entradas(caso.entradas)
    diferencias = verificar_preparacion(caso.entradas, caso.entradas_preparadas, caso.preparacion)
    if diferencias:
        raise ValueError(f"entradas_preparadas no coincide con la preparación: {diferencias[0]}")
    return leer_entradas(caso.entradas_preparadas)


def calcular(caso: Caso) -> dict[str, Tabla]:
    """Calcula las salidas del caso (capa A) con SQLite. Aplica el orden declarado."""
    sentencias = sentencias_proc_sql(caso.programa.read_text(encoding="utf-8"))
    salidas = ejecutar_proc_sql(sentencias, _entradas_para_sql(caso), list(caso.salidas))
    if not caso.orden_relevante:
        for tabla in salidas.values():
            tabla.filas = ordenar_filas(tabla.filas)
    return salidas


def ejecutar(caso: Caso, verificar: bool) -> Resultado:
    """Escribe `esperado/` del caso; con `verificar`, compara lo calculado con lo guardado."""
    if caso.capa == "C":
        mensaje = "capa C: esperado a mano, sin oráculo ejecutable"
        return Resultado(caso.nombre, "omitido", [mensaje])
    if caso.capa == "B":
        return Resultado(caso.nombre, "omitido", ["capa B: vectores de semántica pendientes (K06)"])
    try:
        salidas = calcular(caso)
    except (NoSoportado, ErrorSql, ValueError) as error:
        return Resultado(caso.nombre, "falla", [str(error)])
    lineas: list[str] = []
    for nombre, tabla in salidas.items():
        ruta = caso.esperado / f"{nombre}.csv"
        if verificar:
            diferencias = comparar_con_guardado(
                ruta, tabla, caso.tolerancia, caso.orden_relevante
            )
            lineas.extend(f"tabla '{nombre}', {diferencia}" for diferencia in diferencias)
        else:
            escribir_csv(ruta, tabla)
    if verificar:
        return Resultado(caso.nombre, "falla" if lineas else "verificado", lineas)
    return Resultado(caso.nombre, "escrito", [f"tablas: {', '.join(salidas)}"])
