"""Nodo de agregación del plan: `aggregate` a `tAggregateRow`.

Un `GROUP BY` de `PROC SQL` llega al plan como un `aggregate` con las columnas de agrupación y una
lista de agregados escritos como en el SAS (`COUNT(*)`, `SUM(saldo)`, `COUNT(DISTINCT canal)`). La
semántica que se reproduce es la de `sqlproc`:

* `COUNT(*)` cuenta filas; `COUNT(col)` cuenta las que no son faltantes (`IGNORE_NULL` en Talend).
* `SUM`, `AVG`, `MIN` y `MAX` ignoran los faltantes.
* Un faltante en la columna de agrupación forma su propio grupo.

Lo que no sea `FUNCION(columna)` —`SUM(a * b)`, `ROUND(AVG(x), 2)`— necesita una expresión antes del
agregado y hoy queda pendiente con su motivo: no se supone qué columna calculada se quería sumar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sgm.ir.models import Operator
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla

AGREGADO_SIN_TRADUCIR = "P-AGREGADO-SIN-TRADUCIR"
AGREGADO_SIN_COLUMNA = "P-AGREGADO-COLUMNA-DESCONOCIDA"
AGREGADO_SIN_ESQUEMA = "P-AGREGADO-SIN-ESQUEMA"

_LLAMADA = re.compile(
    r"^\s*(?P<funcion>count|sum|avg|mean|min|max)\s*\(\s*(?P<distinto>distinct\s+)?"
    r"(?P<columna>\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)\s*$",
    re.IGNORECASE,
)
# Función de SAS -> `FUNCTION` de `tAggregateRow`.
_FUNCION = {"count": "count", "sum": "sum", "avg": "avg", "mean": "avg", "min": "min", "max": "max"}
_ENTEROS = frozenset({"id_Integer", "id_Long", "id_Short", "id_Byte"})
_REALES = frozenset({"id_Double", "id_Float"})
_NUMERICOS = _ENTEROS | _REALES | {"id_BigDecimal"}


@dataclass
class ResultadoAgregado:
    """El nodo (o `None`), el esquema de salida y lo que quedó pendiente."""

    nodo: Nodo | None = None
    columnas: list[Columna] = field(default_factory=list)
    pendientes: list[PendienteMigracion] = field(default_factory=list)


def _buscar(nombre: str, columnas: list[Columna]) -> Columna | None:
    """Columna de entrada que nombra `nombre`, sin tabla y sin distinguir mayúsculas."""
    buscado = nombre.strip().split(".")[-1].lower()
    return next((c for c in columnas if c.nombre.lower() == buscado), None)


def _tipo_de_salida(funcion: str, entrada: Columna | None) -> str | None:
    """Tipo de la columna que produce el agregado, o `None` si el de la entrada no lo admite."""
    if funcion == "count":
        return "id_Long"
    if entrada is None:
        return None
    if funcion in ("min", "max"):
        return entrada.tipo
    if entrada.tipo not in _NUMERICOS:
        return None
    if funcion == "avg":
        return "id_BigDecimal" if entrada.tipo == "id_BigDecimal" else "id_Double"
    return "id_Long" if entrada.tipo in _ENTEROS else entrada.tipo


def nodo_agregado(
    op: Operator,
    columnas: list[Columna],
    unico: str,
    x: int,
    linea: int | None,
    ruta_java: str | None = None,
) -> ResultadoAgregado:
    """`tAggregateRow` con las columnas de agrupación y un agregado por cada `SELECT` calculado.

    Todo o nada: un agregado perdido cambia el esquema de salida y rompe lo que viene detrás, así
    que si alguno no se puede armar no se escribe el nodo.
    """
    if not columnas:
        motivo = "el operador 'aggregate' no tiene columnas de entrada demostradas: no se escribe"
        return ResultadoAgregado(
            pendientes=[PendienteMigracion(AGREGADO_SIN_ESQUEMA, motivo, linea)]
        )
    pendientes: list[PendienteMigracion] = []
    grupos: list[Columna] = []
    for nombre in op.params.get("group_by") or []:
        columna = _buscar(str(nombre), columnas)
        if columna is None:
            motivo = f"GROUP BY {nombre}: la entrada no tiene esa columna"
            pendientes.append(PendienteMigracion(AGREGADO_SIN_COLUMNA, motivo, linea))
        else:
            grupos.append(columna)
    operaciones: list[tuple[str, str]] = []
    salida: list[Columna] = list(grupos)
    for agregado in op.params.get("aggregations") or []:
        texto = str(agregado.get("expression") or "")
        alias = str(agregado.get("alias") or "").strip()
        resuelto = _agregado(texto, alias, columnas, linea)
        if isinstance(resuelto, PendienteMigracion):
            pendientes.append(resuelto)
            continue
        celdas, columna_salida = resuelto
        operaciones += celdas
        salida.append(columna_salida)
    for pendiente in op.params.get("pendiente") or []:
        motivo = (
            f"columna sin agregar '{pendiente}': SAS la repite en cada fila y no hay equivalente"
        )
        pendientes.append(PendienteMigracion(AGREGADO_SIN_TRADUCIR, motivo, linea))
    if pendientes or not salida:
        return ResultadoAgregado(columnas=salida, pendientes=pendientes)
    tablas = {"OPERATIONS": tuple(operaciones)}
    if grupos:
        celdas = [
            celda
            for g in grupos
            for celda in (("OUTPUT_COLUMN", g.nombre), ("INPUT_COLUMN", g.nombre))
        ]
        tablas["GROUPBYS"] = tuple(celdas)
    nodo = nodo_desde_plantilla(
        "tAggregateRow", unico, x, 0, tablas=tablas, columnas=list(salida), ruta_java=ruta_java
    )
    return ResultadoAgregado(nodo=nodo, columnas=salida)


def _agregado(
    texto: str, alias: str, columnas: list[Columna], linea: int | None
) -> tuple[list[tuple[str, str]], Columna] | PendienteMigracion:
    """Las cuatro celdas del agregado y su columna de salida, o el pendiente que lo explica."""
    llamada = _LLAMADA.match(texto)
    if llamada is None:
        motivo = (
            f"'{texto}': solo se traduce FUNCION(columna); lo demás necesita una expresión antes"
        )
        return PendienteMigracion(AGREGADO_SIN_TRADUCIR, motivo, linea)
    funcion = llamada["funcion"].lower()
    nombre = llamada["columna"]
    distinto = llamada["distinto"] is not None
    if nombre == "*":
        if funcion != "count" or distinto:
            return PendienteMigracion(
                AGREGADO_SIN_TRADUCIR, f"'{texto}': '*' solo vale para COUNT(*)", linea
            )
        entrada = columnas[0]  # cualquier columna sirve: se cuentan filas, no valores
        ignora_nulos = "false"
    else:
        entrada = _buscar(nombre, columnas)
        if entrada is None:
            motivo = f"'{texto}': la entrada no tiene la columna '{nombre}'"
            return PendienteMigracion(AGREGADO_SIN_COLUMNA, motivo, linea)
        ignora_nulos = "true"
    if distinto and funcion != "count":
        motivo = f"'{texto}': solo COUNT admite DISTINCT"
        return PendienteMigracion(AGREGADO_SIN_TRADUCIR, motivo, linea)
    tipo = _tipo_de_salida(funcion, None if nombre == "*" else entrada)
    if tipo is None:
        motivo = (
            f"'{texto}': la columna '{entrada.nombre}' no es numérica, y {funcion.upper()} lo exige"
        )
        return PendienteMigracion(AGREGADO_SIN_TRADUCIR, motivo, linea)
    destino = alias or f"{funcion}_{entrada.nombre}"
    celdas = [
        ("OUTPUT_COLUMN", destino),
        ("FUNCTION", "distinct" if distinto else _FUNCION[funcion]),
        ("INPUT_COLUMN", entrada.nombre),
        ("IGNORE_NULL", ignora_nulos),
    ]
    return celdas, Columna(destino, tipo)


__all__ = ["ResultadoAgregado", "nodo_agregado"]
