"""Bloque `esquemas` de `caso.yaml`: tipos de columna que el SAS del caso demuestra.

Forma:

    esquemas:
      WORK.nombre_tabla:
        columna_a: {tipo: String, longitud: 5, linea: 12}   # el SAS lo demuestra en esa línea
        columna_b: {tipo: pendiente, motivo: "PROC IMPORT CSV sin LENGTH; el tipo lo fija el dato"}

Reglas:
- Un tipo demostrado trae `linea` (línea del `programa.sas` que lo prueba). `longitud` es opcional y
  solo aplica a `String`.
- Un tipo no demostrado es `pendiente` y trae `motivo`. No se inventa un tipo: si el SAS no lo
  demuestra, queda pendiente (AGENTS.md, regla 6).
- Los tipos son los de `ir/models.py` (`Column.type`): String, Integer, Long, Double, BigDecimal,
  Date, Boolean.
"""

from __future__ import annotations

import re
from typing import Any

TIPOS = frozenset({"String", "Integer", "Long", "Double", "BigDecimal", "Date", "Boolean"})
_TABLA = re.compile(r"(?:[A-Za-z_]\w*\.)?[A-Za-z_]\w*$")
_COLUMNA = re.compile(r"[A-Za-z_]\w*$")


def validar(bloque: Any) -> dict[str, dict[str, dict[str, Any]]]:
    """Valida el bloque `esquemas` y devuelve una copia normalizada.

    Lanza ValueError si el bloque no cumple las reglas del módulo.
    """
    if not isinstance(bloque, dict) or not bloque:
        raise ValueError("'esquemas' debe ser un mapa no vacío de tabla a columnas")
    salida: dict[str, dict[str, dict[str, Any]]] = {}
    for tabla, columnas in bloque.items():
        if not isinstance(tabla, str) or not _TABLA.match(tabla):
            raise ValueError(f"'esquemas': nombre de tabla no válido: {tabla!r}")
        if not isinstance(columnas, dict) or not columnas:
            raise ValueError(f"'esquemas.{tabla}' debe ser un mapa de columnas no vacío")
        salida[tabla] = {}
        for columna, entrada in columnas.items():
            if not isinstance(columna, str) or not _COLUMNA.match(columna):
                raise ValueError(f"'esquemas.{tabla}': nombre de columna no válido: {columna!r}")
            salida[tabla][columna] = _entrada(f"{tabla}.{columna}", entrada)
    return salida


def _entrada(ruta: str, entrada: Any) -> dict[str, Any]:
    if not isinstance(entrada, dict):
        raise ValueError(f"'esquemas.{ruta}' debe ser un mapa con 'tipo'")
    tipo = entrada.get("tipo")
    if tipo == "pendiente":
        motivo = entrada.get("motivo")
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError(f"'esquemas.{ruta}': un tipo pendiente necesita 'motivo'")
        extra = set(entrada) - {"tipo", "motivo"}
        if extra:
            raise ValueError(f"'esquemas.{ruta}': campos no reconocidos {sorted(extra)}")
        return {"tipo": "pendiente", "motivo": motivo}
    if tipo not in TIPOS:
        raise ValueError(f"'esquemas.{ruta}': 'tipo' debe ser {sorted(TIPOS)} o 'pendiente'")
    linea = entrada.get("linea")
    if isinstance(linea, bool) or not isinstance(linea, int) or linea < 1:
        raise ValueError(f"'esquemas.{ruta}': un tipo demostrado necesita 'linea' (entero >= 1)")
    longitud = entrada.get("longitud")
    if longitud is not None:
        if tipo != "String":
            raise ValueError(f"'esquemas.{ruta}': 'longitud' solo aplica a String")
        if isinstance(longitud, bool) or not isinstance(longitud, int) or longitud < 1:
            raise ValueError(f"'esquemas.{ruta}': 'longitud' debe ser entero >= 1")
    extra = set(entrada) - {"tipo", "linea", "longitud"}
    if extra:
        raise ValueError(f"'esquemas.{ruta}': campos no reconocidos {sorted(extra)}")
    normal: dict[str, Any] = {"tipo": tipo, "linea": linea}
    if longitud is not None:
        normal["longitud"] = longitud
    return normal
