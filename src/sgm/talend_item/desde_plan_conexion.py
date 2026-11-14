"""Parámetros de conexión y lectura segura del contexto local de desarrollo."""

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
VARIABLES_POSTGRES: tuple[str, ...] = ("pg_host", "pg_puerto", "pg_base")
_VARIABLES_POR_MOTOR = {"impala": VARIABLES_BASE, "postgres": VARIABLES_POSTGRES}
_CLAVE_SENSIBLE = re.compile(r"pass|pwd|secret|token|clave", re.IGNORECASE)
_CLAVES_META = {"_nota"}


def variables_de_motor(motor: str) -> tuple[str, ...]:
    """Variables de contexto permitidas para un motor compatible."""
    try:
        return _VARIABLES_POR_MOTOR[motor.casefold()]
    except KeyError as error:
        raise ValueError(f"motor de conexión sin soporte: {motor}") from error


def parametros_conexion(en_contexto: bool, motor: str = "impala") -> dict[str, str]:
    """Devuelve referencias de contexto; nunca toma host, usuario o clave del SAS."""
    motor = motor.casefold()
    campos = ("HOST", "PORT", "DBNAME")
    parametros = {nombre: java("") for nombre in campos}
    if en_contexto:
        variables = variables_de_motor(motor)
        prefijo = "impala" if motor == "impala" else "pg"
        parametros.update(
            {
                "HOST": f"context.{variables[0]}",
                "PORT": f"Integer.parseInt(context.{variables[1]})",
                "DBNAME": f"context.{variables[2]}",
            }
        )
        if motor == "impala":
            parametros["IMPALA_ADDITIONAL_JDBC"] = "context.impala_jdbc_extra"
        elif motor == "postgres":
            parametros["USER"] = java("")
            parametros["PASS"] = "((String)null)"
        else:  # pragma: no cover - variables_de_motor limita los valores
            raise ValueError(f"motor de conexión sin soporte: {prefijo}")
    return parametros


def cargar_contexto_dev(ruta: Path) -> dict[str, str]:
    """Lee las cuatro variables locales y rechaza credenciales o claves fuera del contrato."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ValueError("El contexto DEV debe ser un objeto JSON")

    sensibles = sorted(clave for clave in datos if _CLAVE_SENSIBLE.search(clave))
    if sensibles:
        raise ValueError(f"El contexto DEV no admite claves de credenciales: {sensibles}")

    todas = {nombre for variables in _VARIABLES_POR_MOTOR.values() for nombre in variables}
    desconocidas = sorted(set(datos) - todas - _CLAVES_META)
    if desconocidas:
        raise ValueError(f"El contexto DEV tiene claves desconocidas: {desconocidas}")
    motores = [
        motor
        for motor, variables in _VARIABLES_POR_MOTOR.items()
        if any(clave in datos for clave in variables)
    ]
    if not motores:
        raise ValueError("El contexto DEV debe declarar variables de impala o postgres")
    variables_motor = tuple(
        clave for motor in motores for clave in _VARIABLES_POR_MOTOR[motor]
    )
    faltantes = [clave for clave in variables_motor if clave not in datos]
    if faltantes:
        raise ValueError(f"Faltan variables en el contexto DEV: {faltantes}")

    no_textuales = [clave for clave in variables_motor if not isinstance(datos[clave], str)]
    if no_textuales:
        raise ValueError(f"Las variables del contexto DEV deben ser texto: {no_textuales}")
    if "_nota" in datos and not isinstance(datos["_nota"], str):
        raise ValueError("La nota del contexto DEV debe ser texto")
    return {clave: datos[clave] for clave in variables_motor}


__all__ = [
    "VARIABLES_BASE",
    "VARIABLES_POSTGRES",
    "cargar_contexto_dev",
    "parametros_conexion",
    "variables_de_motor",
]
