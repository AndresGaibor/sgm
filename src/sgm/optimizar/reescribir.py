"""Reescritura del segundo paso de una fusión: lo que nombraba de la intermedia, en su origen."""

from __future__ import annotations

import copy
from dataclasses import dataclass

from sgm.ir.models import Operator, Plan
from sgm.optimizar.forma import Forma, NoFusionable, nombre_tabla, parte_de_paso
from sgm.optimizar.sustituir import es_columna, sustituir


@dataclass
class Primero:
    """Lo que el primer paso entrega, para reescribir lo que el segundo nombra."""

    tabla: str  # nombre de la intermedia, sin biblioteca
    principal: str  # conjunto de datos del que parte el primero
    con_cruce: bool
    objetivos: dict[str, dict]  # columna de la intermedia -> su asignación
    estrellas: list[str]  # tablas de las que el primero pasa todas las columnas (`t.*`)
    asignaciones: list[dict] | None  # `None`: el primero no proyecta, pasa la fila entera

    def columna(self, nombre: str, calificada: bool, segundo_cruza: bool) -> str | None:
        asignacion = self.objetivos.get(nombre)
        if asignacion is not None:
            if isinstance(asignacion.get("conditional"), dict):
                raise NoFusionable(f"la columna '{nombre}' sale de un IF/THEN del primer paso")
            texto = str(asignacion.get("expression") or "").strip()
            return texto if es_columna(texto) else f"({texto})"
        if self.asignaciones is None:
            origenes = [] if self.con_cruce else [nombre_tabla(self.principal)]
        else:
            origenes = self.estrellas
        if not calificada:
            if not origenes:
                return None  # no es del primero: es de otra entrada del segundo
            if segundo_cruza:
                raise NoFusionable(f"no se sabe de qué tabla es la columna '{nombre}'")
            if not self.con_cruce:
                return None  # una sola tabla debajo: el nombre significa lo mismo
        if len(origenes) != 1:
            raise NoFusionable(f"no se puede atribuir la columna '{self.tabla}.{nombre}'")
        return f"{origenes[0]}.{nombre}"


def primero_de(plan: Plan, op: Operator, forma: Forma, tabla: str) -> Primero:
    asignaciones = None
    objetivos: dict[str, dict] = {}
    estrellas: list[str] = []
    if forma.proyeccion is not None:
        asignaciones = list((forma.proyeccion.get("params") or {}).get("assignments") or [])
        for asignacion in asignaciones:
            texto = str(asignacion.get("expression") or "").strip()
            if texto == "*":
                raise NoFusionable("el primer paso proyecta `*` sin decir de qué tabla")
            if texto.endswith(".*"):
                estrellas.append(nombre_tabla(texto[:-2]))
            else:
                objetivos[str(asignacion.get("target") or "").strip().lower()] = asignacion
        if not asignaciones:
            asignaciones = None
    return Primero(
        tabla,
        parte_de_paso(plan, op, forma),
        bool(forma.uniones),
        objetivos,
        estrellas,
        asignaciones,
    )


def reescribir(texto: str, primero: Primero, segundo_cruza: bool) -> str:
    def resolver(partes: list[str]) -> str | None:
        if partes[-1] == "*":
            raise NoFusionable("`*` dentro de una expresión")
        if len(partes) >= 2:
            if partes[-2] != primero.tabla:
                return None
            return primero.columna(partes[-1], True, segundo_cruza)
        return primero.columna(partes[0], False, segundo_cruza)

    return sustituir(texto, resolver)


def asignacion_reescrita(asignacion: dict, primero: Primero, cruza: bool) -> dict:
    nueva = copy.deepcopy(asignacion)
    nueva["expression"] = reescribir(str(asignacion.get("expression") or ""), primero, cruza)
    if nueva.get("origin") == "columna" and not es_columna(nueva["expression"]):
        nueva["origin"] = "expresion"
    condicional = nueva.get("conditional")
    if isinstance(condicional, dict):
        for clave in ("condition", "otherwise"):
            if condicional.get(clave) is not None:
                condicional[clave] = reescribir(str(condicional[clave]), primero, cruza)
        for rama in condicional.get("branches") or []:
            for clave in ("condition", "expression"):
                if rama.get(clave) is not None:
                    rama[clave] = reescribir(str(rama[clave]), primero, cruza)
    return nueva


def proyeccion_fundida(segundo: Forma, primero: Primero, a: Forma, salidas: list) -> dict | None:
    cruza = bool(segundo.uniones)
    if segundo.proyeccion is None:
        if a.proyeccion is None:
            return None
        paso = copy.deepcopy(a.proyeccion)
        paso["params"]["outputs"] = list(salidas)
        return paso
    paso = copy.deepcopy(segundo.proyeccion)
    nuevas: list[dict] = []
    agrega = (paso.get("params") or {}).get("modo") == "agrega"
    if agrega and a.proyeccion is not None:
        nuevas.extend(copy.deepcopy((a.proyeccion.get("params") or {}).get("assignments") or []))
    for asignacion in paso["params"].get("assignments") or []:
        texto = str(asignacion.get("expression") or "").strip()
        estrella = texto == "*" and not cruza
        if estrella or (texto.endswith(".*") and nombre_tabla(texto[:-2]) == primero.tabla):
            if primero.asignaciones is not None:
                nuevas += copy.deepcopy(primero.asignaciones)
            elif not primero.con_cruce:
                origen = nombre_tabla(primero.principal)
                nuevas.append({"target": "*", "expression": f"{origen}.*", "origin": "columna"})
            else:
                raise NoFusionable("`*` sobre un cruce sin proyección")
        elif texto.endswith("*"):
            nuevas.append(copy.deepcopy(asignacion))
        else:
            nuevas.append(asignacion_reescrita(asignacion, primero, cruza))
    paso["params"]["assignments"] = nuevas
    return paso


def union_reescrita(union: dict, primero: Primero) -> dict:
    nueva = copy.deepcopy(union)
    params = nueva["params"]
    llaves = []
    for par in params.get("keys") or []:
        reescrito = [reescribir(str(lado), primero, True) for lado in par]
        if not all(es_columna(lado) for lado in reescrito):
            raise NoFusionable("la llave de un cruce es una columna calculada en el paso anterior")
        llaves.append(reescrito)
    params["keys"] = llaves
    if isinstance(params.get("condition"), str):
        params["condition"] = reescribir(params["condition"], primero, True)
    params["sources"] = [
        primero.principal if nombre_tabla(fuente) == primero.tabla else fuente
        for fuente in params.get("sources") or []
    ]
    return nueva


__all__ = ["Primero", "proyeccion_fundida", "reescribir", "primero_de", "union_reescrita"]
