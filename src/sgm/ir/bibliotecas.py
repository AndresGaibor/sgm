"""Resolución de librefs SAS mediante decisiones explícitas por programa."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

import yaml

from sgm.frontend.libnames import InfoLibname

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_MOTORES = frozenset({"impala", "postgres"})


def resolver_biblioteca(
    tabla: str,
    bibliotecas: Mapping[str, InfoLibname],
    decisiones: Mapping[str, dict],
) -> tuple[str, str] | None:
    """Resuelve `lz.cuentas` a un motor y nombre remoto solo con una decisión validada."""
    if "." not in tabla:
        return None
    libref, miembro = tabla.split(".", 1)
    libref = libref.casefold()
    info = next(
        (dato for nombre, dato in bibliotecas.items() if nombre.casefold() == libref), None
    )
    decision = next(
        (dato for nombre, dato in decisiones.items() if nombre.casefold() == libref), None
    )
    if info is None or info.motor is None or decision is None:
        return None
    if info.motor not in _MOTORES:
        raise ValueError(f"motor LIBNAME sin soporte: {info.motor}")
    if not isinstance(decision, Mapping) or set(decision) != {"motor", "base"}:
        raise ValueError(f"decisión inválida para libref {libref}: se requieren motor y base")
    motor, base = decision.get("motor"), decision.get("base")
    if not isinstance(motor, str) or motor.casefold() != info.motor:
        raise ValueError(f"el motor decidido para {libref} no coincide con LIBNAME")
    if not isinstance(base, str) or not _IDENTIFIER.fullmatch(base):
        raise ValueError(f"la base decidida para {libref} debe ser un identificador SQL simple")
    if not _IDENTIFIER.fullmatch(miembro):
        raise ValueError(f"el miembro de {libref} no es un identificador SQL simple")
    return info.motor, f"{base}.{miembro.lower()}"


def cargar_decisiones_libnames(ruta: Path | None) -> dict[str, dict[str, str]]:
    """Lee solo `{motor, base}` por libref; ignora valores desconocidos rechazándolos."""
    if ruta is None:
        return {}
    try:
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError("el archivo de decisiones no contiene YAML válido") from error
    if not isinstance(datos, dict) or set(datos) != {"libnames"}:
        raise ValueError("el archivo debe contener únicamente el mapa 'libnames'")
    crudos = datos.get("libnames")
    if not isinstance(crudos, dict):
        raise ValueError("'libnames' debe ser un mapa de libref a decisión")
    decisiones: dict[str, dict[str, str]] = {}
    for nombre, decision in crudos.items():
        clave = str(nombre).casefold()
        if not _IDENTIFIER.fullmatch(clave):
            raise ValueError("el libref de una decisión debe ser un identificador SAS simple")
        if not isinstance(decision, dict) or set(decision) != {"motor", "base"}:
            raise ValueError(f"decisión inválida para libref {clave}: se requieren motor y base")
        motor, base = decision.get("motor"), decision.get("base")
        if not isinstance(motor, str) or motor.casefold() not in _MOTORES:
            raise ValueError(f"motor sin soporte en decisión de libref {clave}")
        if not isinstance(base, str) or not _IDENTIFIER.fullmatch(base):
            raise ValueError(f"base inválida en decisión de libref {clave}")
        decisiones[clave] = {"motor": motor.casefold(), "base": base}
    return decisiones


__all__ = ["cargar_decisiones_libnames", "resolver_biblioteca"]
