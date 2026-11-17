"""EXISTS correlacionado de una sola igualdad en el intérprete del anillo B (plan C, C-9).

`EXISTS (SELECT ... FROM T p WHERE p.k = v.k)` equivale a `v.k IN (valores de p.k)`. Esa
equivalencia solo vale si ninguna llave es faltante: la guía (lrcon, p. 154) dice que los faltantes
son los más bajos en cualquier comparación, pero no dice si un faltante es igual a otro. Con un
faltante en alguna llave la subconsulta se rechaza.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlglot import exp

from sgm.migrar import semantica
from sgm.migrar.interprete_subconsultas_orden import SubconsultaNoSoportada

Filtrar = Callable[[list[dict], str, dict | None], list[dict]]
Columna = Callable[[dict, str], object]


def _igualdad(select: exp.Select) -> tuple[str, str, str, str] | None:
    """(alias de la fuente, columna interna, calificador externo, columna externa) o None."""
    where = select.args.get("where")
    if not isinstance(where, exp.Where) or not isinstance(where.this, exp.EQ):
        return None
    izquierda, derecha = where.this.left, where.this.right
    if not (isinstance(izquierda, exp.Column) and isinstance(derecha, exp.Column)):
        return None
    desde = select.args.get("from_")
    fuente = desde.this if isinstance(desde, exp.From) else None
    if not isinstance(fuente, exp.Table):
        return None
    alias = (fuente.alias or fuente.name).lower()
    for dentro, fuera in ((izquierda, derecha), (derecha, izquierda)):
        interna_ok = dentro.table and dentro.table.lower() == alias
        externa_ok = fuera.table and fuera.table.lower() != alias
        if interna_ok and externa_ok:
            return fuente.name.lower(), dentro.name.lower(), fuera.table.lower(), fuera.name.lower()
    return None


def reescribir_exists(
    arbol: exp.Expression,
    filas: list[dict],
    tablas: dict[str, list[dict]] | None,
    *,
    filtrar: Filtrar,
    columna: Columna,
    literal: Callable[[object], exp.Expression],
) -> exp.Expression:
    """Sustituye cada EXISTS correlacionado simple por un IN sobre la columna externa.

    Devuelve la expresión resultante: si el EXISTS es la raíz, la raíz cambia.
    """
    raiz = arbol
    for nodo in list(arbol.find_all(exp.Exists)):
        if tablas is None:
            raise SubconsultaNoSoportada("EXISTS requiere el contexto de tablas")
        select = nodo.this if isinstance(nodo.this, exp.Select) else None
        forma = _igualdad(select) if select is not None else None
        if forma is None:
            raise SubconsultaNoSoportada("EXISTS solo se resuelve con una igualdad correlacionada")
        nombre, interna, _, externa = forma
        filas_interna = tablas.get(nombre)
        if not filas_interna:
            raise SubconsultaNoSoportada(f"la fuente '{nombre}' no está disponible")
        llaves = [fila for fila in filas_interna]
        if any(semantica.es_faltante(_valor(fila, interna, columna)) for fila in llaves):
            raise SubconsultaNoSoportada("EXISTS con llave faltante en la subconsulta")
        if any(semantica.es_faltante(columna(fila, externa)) for fila in filas):
            raise SubconsultaNoSoportada("EXISTS con llave externa faltante")
        valores = [_valor(fila, interna, columna) for fila in llaves]
        if not valores:
            raise SubconsultaNoSoportada("EXISTS sobre una tabla vacía no se resuelve")
        pertenece = exp.In(
            this=exp.column(externa),
            expressions=[literal(valor) for valor in dict.fromkeys(valores)],
        )
        if nodo is raiz:
            raiz = pertenece
        else:
            nodo.replace(pertenece)
    return raiz


def _valor(fila: dict, nombre: str, columna: Columna) -> object:
    return columna(fila, nombre)
