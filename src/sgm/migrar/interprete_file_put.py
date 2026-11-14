"""Interpretación conservadora de `PUT` en lista con `FILE DSD` delimitado."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from sgm.ir.models import Plan
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete


def escribir_lista(
    filas: Sequence[Mapping[str, object]],
    variables: Sequence[str],
    dlm: str,
    dsd: bool,
) -> list[str]:
    """Serializa una fila por línea cuando las reglas de `FILE`/`PUT` están demostradas.

    Los faltantes se dejan pendientes: la referencia de `PUT` advierte que `DSD` puede
    suprimirlos y no fija aquí un resultado estable para este caso.
    """
    if len(dlm) != 1:
        raise NoSoportadoEnInterprete("put", "P-FILE-DLM-SIN-SOPORTE")
    resultado: list[str] = []
    for fila in filas:
        campos: list[str] = []
        for variable in variables:
            valor = next(
                (
                    dato
                    for nombre, dato in fila.items()
                    if str(nombre).casefold() == variable.casefold()
                ),
                None,
            )
            if valor is None:
                codigo = "P-FILE-DSD-MISSING" if dsd else "P-FILE-MISSING"
                raise NoSoportadoEnInterprete("put", codigo)
            if isinstance(valor, (int, float, Decimal)):
                raise NoSoportadoEnInterprete("put", "P-PUT-NUMERIC-FORMAT")
            campo = str(valor)
            if "\r" in campo or "\n" in campo:
                raise NoSoportadoEnInterprete("put", "P-FILE-SALTO-LINEA")
            contiene_delimitador = dlm in campo
            if contiene_delimitador and not dsd:
                raise NoSoportadoEnInterprete("put", "P-FILE-DSD-COMILLAS")
            if dsd and '"' in campo and not contiene_delimitador:
                raise NoSoportadoEnInterprete("put", "P-FILE-DSD-COMILLAS")
            if dsd and contiene_delimitador:
                campo = '"' + campo.replace('"', '""') + '"'
            campos.append(campo)
        resultado.append(dlm.join(campos))
    return resultado


def escribir_archivos_plan(
    plan: Plan, tablas: Mapping[str, Sequence[Mapping[str, object]]]
) -> dict[str, list[str]]:
    """Renderiza los `write_file` de DATA step soportados sin tocar el sistema de archivos."""
    resultado: dict[str, list[str]] = {}
    for operador in plan.graph.operators():
        if operador.kind != "write_file" or not operador.params.get("variables"):
            continue
        entradas = operador.params.get("inputs") or []
        if len(entradas) != 1:
            raise NoSoportadoEnInterprete("put", "P-FILE-PUT-ORIGEN-SIN-SOPORTE")
        nombre_entrada = str(entradas[0]).split(".")[-1].casefold()
        filas = next(
            (
                datos
                for nombre, datos in tablas.items()
                if str(nombre).split(".")[-1].casefold() == nombre_entrada
            ),
            None,
        )
        if filas is None:
            raise NoSoportadoEnInterprete("put", "P-FILE-PUT-ORIGEN-AUSENTE")
        destino = str(operador.params.get("outfile") or "").strip()
        if len(destino) >= 2 and destino[0] == destino[-1] and destino[0] in "'\"":
            cita = destino[0]
            destino = destino[1:-1].replace(cita + cita, cita)
        if not destino or "&" in destino:
            raise NoSoportadoEnInterprete("put", "P-FILE-RUTA-DINAMICA")
        if destino in resultado:
            raise NoSoportadoEnInterprete("put", "P-FILE-RUTA-DUPLICADA")
        resultado[destino] = escribir_lista(
            filas,
            [str(variable) for variable in operador.params["variables"]],
            str(operador.params.get("delimiter") or " "),
            bool(operador.params.get("dsd")),
        )
    return resultado


__all__ = ["escribir_archivos_plan", "escribir_lista"]
