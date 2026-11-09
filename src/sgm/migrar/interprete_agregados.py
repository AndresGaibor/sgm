"""Evaluación acotada de agregados PROC SQL para el intérprete de referencia."""

from __future__ import annotations

import re
from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from sqlglot import exp

from sgm.migrar import semantica

_AGREGADO = re.compile(r"(?is)^\s*(count|sum|avg|mean|min|max)\s*\((.*)\)\s*$")
_COLUMNA_SIMPLE = re.compile(r"(?i)^(?:[a-z_]\w*\.)*([a-z_]\w*)$")
_ALIAS_SIMPLE = re.compile(r"(?i)^[a-z_]\w*$")


class AgregadoNoSoportado(ValueError):
    """Forma de agregado que esta implementación no puede interpretar con seguridad."""


def agregar(
    filas: list[dict],
    params: dict,
    *,
    parsear: Callable[[str], exp.Expression],
    evaluar: Callable[[exp.Expression, dict], object],
    columna: Callable[[dict, str], object],
) -> list[dict]:
    """Ejecuta los agregados demostrados por la IR sin adivinar tipos de grupo."""
    if params.get("pendiente"):
        raise AgregadoNoSoportado("columnas sin agregar en el SELECT")
    agregaciones = params.get("aggregations") or []
    if not agregaciones:
        raise AgregadoNoSoportado("GROUP BY sin agregado no está implementado")

    columnas_grupo = []
    for expresion in params.get("group_by") or []:
        coincidencia = _COLUMNA_SIMPLE.fullmatch(str(expresion).strip())
        if coincidencia is None:
            raise AgregadoNoSoportado(f"clave GROUP BY no simple: {expresion}")
        nombre = coincidencia.group(1).lower()
        if nombre in columnas_grupo:
            raise AgregadoNoSoportado(f"clave GROUP BY duplicada: {nombre}")
        columnas_grupo.append(nombre)

    group_outputs = params.get("group_outputs")
    if group_outputs is None:
        group_outputs = [{"expression": nombre, "alias": nombre} for nombre in columnas_grupo]
    salidas_grupo = []
    nombres_salida = []
    for group_output in group_outputs:
        if not isinstance(group_output, dict):
            raise AgregadoNoSoportado("proyección de GROUP BY no válida")
        expresion = str(group_output.get("expression") or "").strip()
        coincidencia = _COLUMNA_SIMPLE.fullmatch(expresion)
        alias = str(group_output.get("alias") or "").strip()
        if coincidencia is None or not _ALIAS_SIMPLE.fullmatch(alias):
            raise AgregadoNoSoportado(f"columna de salida GROUP BY no soportada: {expresion}")
        origen = coincidencia.group(1).lower()
        if origen not in columnas_grupo:
            raise AgregadoNoSoportado(f"la columna de salida '{origen}' no está en GROUP BY")
        destino = alias.lower()
        if destino in nombres_salida:
            raise AgregadoNoSoportado(f"alias de salida repetido: {destino}")
        nombres_salida.append(destino)
        salidas_grupo.append((origen, destino))

    operaciones = []
    for agregacion in agregaciones:
        expresion = str(agregacion.get("expression") or "").strip()
        alias = str(agregacion.get("alias") or "").strip()
        coincidencia = _AGREGADO.fullmatch(expresion)
        if coincidencia is None or not _ALIAS_SIMPLE.fullmatch(alias):
            raise AgregadoNoSoportado(f"agregado o alias no soportado: {expresion}")
        funcion = coincidencia.group(1).lower()
        argumento = coincidencia.group(2).strip()
        if funcion == "count" and argumento == "*":
            arbol = None
        elif argumento == "*" or re.match(r"(?i)^distinct\b", argumento):
            raise AgregadoNoSoportado(f"forma no soportada: {expresion}")
        else:
            arbol = parsear(argumento)
        destino = alias.lower()
        if destino in nombres_salida:
            raise AgregadoNoSoportado(f"alias de salida repetido: {destino}")
        nombres_salida.append(destino)
        operaciones.append((funcion, arbol, destino, expresion))

    def tiene_columna(fila: dict, nombre: str) -> bool:
        return any(str(clave).lower() == nombre.lower() for clave in fila)

    grupos: dict[tuple, tuple[dict, list[dict]]] = {}
    if not columnas_grupo:
        grupos[()] = ({}, list(filas))
    else:
        for fila in filas:
            llave = []
            valores_grupo = {}
            for nombre in columnas_grupo:
                if not tiene_columna(fila, nombre):
                    raise AgregadoNoSoportado(f"falta la columna de agrupación '{nombre}'")
                valor = columna(fila, nombre)
                valores_grupo[nombre] = semantica.a_texto(valor)
                if semantica.es_faltante(valor):
                    llave.append(("faltante",))
                elif isinstance(valor, (int, float, Decimal)) and not isinstance(valor, bool):
                    llave.append(("numero", Decimal(str(valor))))
                elif isinstance(valor, str):
                    texto = semantica.como_texto(valor)
                    if semantica.como_numero(texto) is not None:
                        raise AgregadoNoSoportado(
                            f"tipo numérico o carácter ambiguo para la clave '{nombre}'"
                        )
                    llave.append(("texto", texto))
                else:
                    raise AgregadoNoSoportado(f"tipo no soportado para la clave '{nombre}'")
            clave = tuple(llave)
            if clave not in grupos:
                grupos[clave] = (valores_grupo, [])
            grupos[clave][1].append(fila)

    def numero(valor: object, expresion: str) -> Decimal | None:
        if semantica.es_faltante(valor):
            return None
        convertido = semantica.como_numero(valor)
        if convertido is None:
            raise AgregadoNoSoportado(
                f"la expresión numérica '{expresion}' contiene un valor no numérico"
            )
        try:
            return Decimal(str(valor).strip())
        except InvalidOperation:
            return Decimal(str(convertido))

    def texto_decimal(valor: Decimal | None) -> str | None:
        if valor is None:
            return None
        if valor == 0:
            return "0"
        return format(valor.normalize(), "f")

    resultado = []
    for valores_grupo, miembros in grupos.values():
        salida = {alias: valores_grupo[nombre] for nombre, alias in salidas_grupo}
        for funcion, arbol, destino, expresion in operaciones:
            if arbol is None:
                salida[destino] = str(len(miembros))
                continue
            valores = []
            for fila in miembros:
                for columna_exp in arbol.find_all(exp.Column):
                    if not tiene_columna(fila, columna_exp.name):
                        raise AgregadoNoSoportado(
                            f"falta la columna '{columna_exp.name}' en '{expresion}'"
                        )
                valor = evaluar(arbol, fila)
                if funcion == "count":
                    if not semantica.es_faltante(valor):
                        valores.append(valor)
                else:
                    convertido = numero(valor, expresion)
                    if convertido is not None:
                        valores.append(convertido)
            if funcion == "count":
                salida[destino] = str(len(valores))
            elif not valores:
                salida[destino] = None
            elif funcion == "sum":
                salida[destino] = texto_decimal(sum(valores, Decimal(0)))
            elif funcion in ("avg", "mean"):
                salida[destino] = texto_decimal(sum(valores, Decimal(0)) / len(valores))
            elif funcion == "min":
                salida[destino] = texto_decimal(min(valores))
            elif funcion == "max":
                salida[destino] = texto_decimal(max(valores))
        output_order = params.get("output_order")
        if output_order is not None:
            nombres = [str(nombre).lower() for nombre in output_order]
            if len(nombres) != len(set(nombres)) or set(nombres) != set(salida):
                raise AgregadoNoSoportado("proyección de salida incompleta o duplicada")
            salida = {nombre: salida[nombre] for nombre in nombres}
        resultado.append(salida)
    return resultado
