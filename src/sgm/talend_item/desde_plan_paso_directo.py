"""Lector Talend para una consulta SQL pass-through de PROC SQL."""

from __future__ import annotations

import re
from pathlib import Path

import sqlglot
from sqlglot import exp

from sgm.ir.models import Column, Operator
from sgm.java_identificadores import is_java_identifier
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.desde_plan_conexion import parametros_conexion
from sgm.talend_item.desde_plan_nodos import Resultado, columnas_talend
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.plantillas import nodo_desde_plantilla

_LITERALES_Y_COMENTARIOS = re.compile(
    r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|--[^\r\n]*|/\*.*?\*/", re.DOTALL
)
_MACRO = re.compile(r"&{1,2}[A-Za-z_]\w*\.?", re.IGNORECASE)
_COMPONENTES = {"impala": "tImpalaInput", "postgres": "tPostgresqlInput"}
_TIPOS_AGREGADOS = {"count": "Long", "sum": "Double"}


def _dialecto(motor: str) -> str | None:
    return {"impala": "hive", "postgres": "postgres"}.get(motor.lower())


def _tabla(sql: str, motor: str) -> exp.Select | None:
    dialecto = _dialecto(motor)
    if not dialecto:
        return None
    try:
        consulta = sqlglot.parse_one(sql, read=dialecto)
    except sqlglot.errors.SqlglotError:
        return None
    return consulta if isinstance(consulta, exp.Select) else None


def esquema_paso_directo(op: Operator, esquemas: dict[str, list[Column]]) -> list[Column]:
    """Deriva columnas solo de un SELECT y de esquemas locales conocidos de sus fuentes."""
    consulta = _tabla(str(op.params.get("sql") or ""), str(op.params.get("engine") or ""))
    if consulta is None:
        return []
    tablas = list(consulta.find_all(exp.Table))
    if not tablas:
        return []
    indice = {nombre.casefold(): columnas for nombre, columnas in esquemas.items()}
    esquemas_fuente: dict[str, list[Column]] = {}
    alias_fuente: dict[str, str] = {}
    for tabla in tablas:
        partes = [str(parte) for parte in (tabla.catalog, tabla.db, tabla.name) if parte]
        if len(partes) > 2:
            return []
        fuente = ".".join(partes).casefold()
        columnas = indice.get(fuente)
        if columnas is None:
            return []
        esquemas_fuente[fuente] = columnas
        alias_fuente[str(tabla.alias_or_name).casefold()] = fuente

    def tipo_columna(columna: exp.Column) -> str | None:
        nombre = columna.name.casefold()
        if columna.table:
            fuente = alias_fuente.get(columna.table.casefold())
            candidatas = [esquemas_fuente.get(fuente, [])] if fuente else []
        else:
            candidatas = list(esquemas_fuente.values())
        coincidencias = [
            col.type
            for esquema in candidatas
            for col in esquema
            if col.name.casefold() == nombre
        ]
        return coincidencias[0] if len(coincidencias) == 1 else None

    proyecciones: list[Column] = []
    for expresion in consulta.expressions:
        if isinstance(expresion, exp.Star):
            if len(esquemas_fuente) != 1:
                return []
            proyecciones.extend(
                Column(col.name, col.type, col.length, "derived")
                for col in next(iter(esquemas_fuente.values()))
            )
            continue
        cuerpo = expresion.this if isinstance(expresion, exp.Alias) else expresion
        alias = expresion.alias if isinstance(expresion, exp.Alias) else None
        if isinstance(cuerpo, exp.Column):
            nombre = alias or cuerpo.name
            tipo = tipo_columna(cuerpo)
        else:
            nombre = alias
            tipo = None
            if isinstance(cuerpo, exp.Func):
                funcion = cuerpo.sql_name().lower()
                tipo = _TIPOS_AGREGADOS.get(funcion)
        if not nombre:
            return []
        proyecciones.append(Column(str(nombre), tipo, source="derived"))
    return proyecciones


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _pendiente(codigo: str, mensaje: str, op: Operator) -> Resultado:
    return Resultado(pendientes=[PendienteMigracion(codigo, mensaje, _linea(op))])


def nodo_paso_directo(
    op: Operator,
    esquema: list[Column],
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
    en_contexto: bool = False,
) -> Resultado:
    """Emite `tImpalaInput` con la consulta original y parámetros sin credenciales."""
    motor = str(op.params.get("engine") or "").lower()
    consulta = str(op.params.get("sql") or "")
    componente = _COMPONENTES.get(motor)
    if componente is None:
        return _pendiente(
            "P-MOTOR-SIN-SOPORTE",
            f"motor '{motor or '(vacío)'}' sin lector pass-through reconocido",
            op,
        )
    if _MACRO.search(_LITERALES_Y_COMENTARIOS.sub(" ", consulta)):
        return _pendiente(
            "P-PASO-DIRECTO-MACRO",
            "la consulta pass-through tiene referencias de macro sin resolver",
            op,
        )
    if not esquema:
        return _pendiente(
            "P-ESQUEMA-VACIO",
            "el SELECT remoto no tiene un esquema de columnas demostrado por catálogo o muestra",
            op,
        )
    if not consulta:
        return _pendiente("P-OPERADOR-SIN-SOPORTE", "consulta pass-through vacía", op)
    if not Path(__file__).parent.joinpath("plantillas", f"{componente}.json").is_file():
        return _pendiente(
            "P-COMPONENTE-SIN-PLANTILLA",
            f"falta una plantilla de Studio verificada para {componente}",
            op,
        )

    nombres = [col.name for col in esquema]
    if (
        len({nombre.casefold() for nombre in nombres}) != len(nombres)
        or any(not is_java_identifier(nombre) for nombre in nombres)
    ):
        return _pendiente(
            "P-ESQUEMA-NO-PORTABLE",
            "el esquema del resultado tiene nombres duplicados o no portables para Talend",
            op,
        )
    columnas = columnas_talend(esquema)
    valores = {
        "QUERY": java(consulta),
        "USE_EXISTING_CONNECTION": "false",
        **parametros_conexion(en_contexto),
    }
    if motor == "impala":
        valores["PASS"] = "((String)null)"
    nodo = nodo_desde_plantilla(
        componente,
        unico,
        x,
        y,
        valores,
        columnas=columnas,
        ruta_java=ruta_java,
    )
    pendientes = []
    sin_tipo = [col.name for col in esquema if col.type is None]
    if sin_tipo:
        pendientes.append(
            PendienteMigracion(
                "P-TIPO-DESCONOCIDO",
                f"resultado pass-through: tipos sin catálogo para {', '.join(sin_tipo)}",
                _linea(op),
            )
        )
    pendientes.append(
        PendienteMigracion(
            "P-CONEXION-BASE",
            (
                f"{unico}: host, puerto y base vienen del contexto DEV; configure QA y PROD"
                if en_contexto
                else f"{unico}: configure la conexión a {motor} en Studio; "
                "no se copian DSN ni credenciales"
            ),
            _linea(op),
        )
    )
    return Resultado(nodo=nodo, columnas=columnas, pendientes=pendientes)


__all__ = ["esquema_paso_directo", "nodo_paso_directo"]
