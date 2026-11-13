"""Parámetros de conexión de `tImpalaRow` y lectura del contexto local de desarrollo."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sgm.talend_item.jobs_diseno import java

VARIABLES_BASE: tuple[str, ...] = (
    "impala_host",
    "impala_puerto",
    "impala_base",
    "impala_jdbc_extra",
)
_CLAVE_SENSIBLE = re.compile(r"pass|pwd|secret|token|clave", re.IGNORECASE)
_CLAVES_META = {"_nota"}


def parametros_conexion(en_contexto: bool) -> dict[str, str]:
    """Devuelve los parámetros de `tImpalaRow` sin incorporar una conexión literal."""
    parametros = {nombre: java("") for nombre in ("HOST", "PORT", "DBNAME")}
    if en_contexto:
        parametros.update(
            {
                "HOST": "context.impala_host",
                "PORT": "Integer.parseInt(context.impala_puerto)",
                "DBNAME": "context.impala_base",
                "IMPALA_ADDITIONAL_JDBC": "context.impala_jdbc_extra",
            }
        )
    return parametros


def cargar_contexto_dev(ruta: Path) -> dict[str, str]:
    """Lee las cuatro variables locales y rechaza credenciales o claves fuera del contrato."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ValueError("El contexto DEV debe ser un objeto JSON")

    sensibles = sorted(clave for clave in datos if _CLAVE_SENSIBLE.search(clave))
    if sensibles:
        raise ValueError(f"El contexto DEV no admite claves de credenciales: {sensibles}")

    desconocidas = sorted(set(datos) - set(VARIABLES_BASE) - _CLAVES_META)
    if desconocidas:
        raise ValueError(f"El contexto DEV tiene claves desconocidas: {desconocidas}")
    faltantes = [clave for clave in VARIABLES_BASE if clave not in datos]
    if faltantes:
        raise ValueError(f"Faltan variables en el contexto DEV: {faltantes}")

    no_textuales = [clave for clave in VARIABLES_BASE if not isinstance(datos[clave], str)]
    if no_textuales:
        raise ValueError(f"Las variables del contexto DEV deben ser texto: {no_textuales}")
    if "_nota" in datos and not isinstance(datos["_nota"], str):
        raise ValueError("La nota del contexto DEV debe ser texto")
    return {clave: datos[clave] for clave in VARIABLES_BASE}


__all__ = ["VARIABLES_BASE", "cargar_contexto_dev", "parametros_conexion"]
