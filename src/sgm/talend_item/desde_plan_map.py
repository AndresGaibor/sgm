"""El `tMap` que sale de un operador `map`: entradas, llaves de unión, asignaciones y filtro.

Un `map` del plan es una cadena de pasos (`join`, `filter`, `derive`, `aggregate`) sobre una o
varias fuentes. El `tMap` hace de una sola vez lo que en SQL son tres cláusulas: las llaves de unión
van en los lookups, las asignaciones del `SELECT` en las expresiones de la salida y el `WHERE` en el
`expressionFilter` de esa misma salida.

Lo que no se puede demostrar no se escribe: un paso sin traducción deja su pendiente y el resto del
mapa se arma igual, para que el Job siga siendo útil y el hueco quede a la vista.

Los nombres de las conexiones los decide este módulo, no el llamador: la fuente principal es `row1`
y los lookups `row2` en adelante, en el orden en que llegaron. `Armado.entradas` devuelve ese
reparto para que el Job conecte cada nodo con el nombre que el `tMap` espera.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.ir.models import Operator
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.desde_plan_expresiones import expresion
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

PRINCIPAL = "row1"
NO_SOPORTADO = "P-OPERADOR-SIN-SOPORTE"
SIN_TRADUCIR = "P-ASIGNACION-SIN-TRADUCIR"
FALLO = "P-FALLO-INTERNO"


@dataclass(frozen=True)
class Fuente:
    """Una entrada del `tMap`: el nodo que la produce y las columnas que trae."""

    origen: str  # UNIQUE_NAME del nodo que la alimenta
    tabla: str  # nombre sin librería, en minúsculas: `ventas`, `clientes`
    columnas: list[Columna] = field(default_factory=list)


@dataclass
class Armado:
    """Resultado de armar el `tMap`: el nodo (si se pudo), el reparto de filas y los pendientes.

    `columnas` es el esquema de la salida y se calcula antes de montar el nodo: aunque el `tMap` no
    se pueda montar, la escritura que viene detrás sigue sabiendo qué columnas tiene que escribir, y
    el fallo queda como pendiente en vez de arrastrar al resto del Job.
    """

    nodo: Nodo | None = None
    entradas: dict[str, str] = field(default_factory=dict)  # origen -> row1, row2, ...
    columnas: list[Columna] = field(default_factory=list)
    pendientes: list[PendienteMigracion] = field(default_factory=list)


@dataclass(frozen=True)
class _Meseta:
    """Las fuentes ya ordenadas: la principal primero, con su nombre de fila y su tipo."""

    fuentes: list[Fuente]

    def fila(self, indice: int) -> str:
        return PRINCIPAL if indice == 0 else f"row{indice + 1}"

    @property
    def filas(self) -> dict[str, set[str]]:
        return {self.fila(i): {c.nombre for c in f.columnas} for i, f in enumerate(self.fuentes)}

    @property
    def tipos(self) -> dict[str, str]:
        return {
            f"{self.fila(i)}.{c.nombre}": c.tipo
            for i, fuente in enumerate(self.fuentes)
            for c in fuente.columnas
        }

    def tipo_de(self, fila: str, columna: str) -> str:
        for indice, fuente in enumerate(self.fuentes):
            if self.fila(indice) != fila:
                continue
            for propia in fuente.columnas:
                if propia.nombre == columna:
                    return propia.tipo
        return "id_String"


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _tabla(calificada: str) -> tuple[str, str]:
    """`work.ventas` o `ventas` a `(tabla, columna)`; `ventas.k` a `(ventas, k)`."""
    partes = [p for p in calificada.strip().lower().split(".") if p]
    if len(partes) >= 2:
        return partes[-2], partes[-1]
    return "", (partes[0] if partes else "")


def _pasos(op: Operator, tipo: str) -> list[dict]:
    return [
        paso.get("params", {}) for paso in op.params.get("steps", []) if paso.get("kind") == tipo
    ]


def _principal(fuentes: list[Fuente], join: dict | None) -> int:
    """Índice de la fuente principal: la que el paso `join` declara como origen del `FROM`.

    En el SAS el `FROM` va primero y los `JOIN` después; `sources` guarda ese primer conjunto. Si no
    hay paso de unión, la principal es la primera entrada, que es el orden en que llegaron las
    aristas.
    """
    if join:
        declaradas = [str(s).lower().split(".")[-1] for s in join.get("sources", [])]
        for indice, fuente in enumerate(fuentes):
            if fuente.tabla in declaradas:
                return indice
    return 0


def _llaves(meseta: _Meseta, join: dict, armado: Armado, op: Operator) -> dict[int, dict]:
    """Por cada lookup, la columna de la unión y su expresión sobre la principal."""
    union: dict[int, dict[str, str]] = {i: {} for i in range(1, len(meseta.fuentes))}
    for par in join.get("keys") or []:
        if len(par) != 2:
            armado.pendientes.append(
                PendienteMigracion(
                    "P-LLAVE-INCOMPLETA", f"llave de unión {par!r} sin las dos columnas", _linea(op)
                )
            )
            continue
        tabla_izq, columna_izq = _tabla(par[0])
        tabla_der, columna_der = _tabla(par[1])
        for indice, fuente in enumerate(meseta.fuentes):
            if indice == 0:
                continue
            if fuente.tabla == tabla_der:
                union[indice][columna_der] = f"{PRINCIPAL}.{columna_izq}"
            elif fuente.tabla == tabla_izq:
                # El `ON` escrito al revés: la principal quedó a la derecha.
                union[indice][columna_izq] = f"{PRINCIPAL}.{columna_der}"
    return union


def _entradas(meseta: _Meseta, join: dict | None, armado: Armado, op: Operator) -> list[EntradaMap]:
    """Entradas del `tMap`: la principal sin unión y cada lookup con sus llaves."""
    if not join:
        return [
            EntradaMap(meseta.fila(i), list(fuente.columnas))
            for i, fuente in enumerate(meseta.fuentes)
        ]
    llaves = _llaves(meseta, join, armado, op)
    interna = str(join.get("join_type", "")).lower() == "inner"
    entradas: list[EntradaMap] = []
    for indice, fuente in enumerate(meseta.fuentes):
        if indice == 0:
            entradas.append(EntradaMap(PRINCIPAL, list(fuente.columnas)))
            continue
        propias = llaves.get(indice, {})
        if not propias:
            armado.pendientes.append(
                PendienteMigracion(
                    "P-UNION-SIN-LLAVES",
                    f"{fuente.tabla}: el SAS no da una llave de unión demostrable "
                    "para esta entrada",
                    _linea(op),
                )
            )
        entradas.append(
            EntradaMap(
                meseta.fila(indice),
                list(fuente.columnas),
                expresiones_union=propias,
                union_interna=interna and bool(propias),
            )
        )
    return entradas


def _filtro(meseta: _Meseta, op: Operator, armado: Armado) -> str:
    """El `WHERE` del SAS como `expressionFilter`, o vacío si no se pudo demostrar."""
    textos = [str(paso.get("expression", "")).strip() for paso in _pasos(op, "filter")]
    textos = [texto for texto in textos if texto]
    if not textos:
        return ""
    texto = " AND ".join(f"({t})" for t in textos)
    traducido, motivo = expresion(texto, meseta.filas, meseta.tipos)
    if traducido is None:
        armado.pendientes.append(
            PendienteMigracion("P-FILTRO-SIN-TRADUCIR", f"filtro '{texto}': {motivo}", _linea(op))
        )
        return ""
    return traducido


def _valor(
    meseta: _Meseta, asignacion: dict, armado: Armado, op: Operator
) -> tuple[str | None, str]:
    """Java de una asignación: la columna tal cual, o la expresión traducida."""
    destino = str(asignacion.get("target", "")).strip()
    valor = str(asignacion.get("expression", "")).strip()
    if asignacion.get("origin") == "columna":
        fila, motivo = _fila_de_columna(meseta, valor)
        if fila is None:
            armado.pendientes.append(
                PendienteMigracion(SIN_TRADUCIR, f"columna '{destino}': {motivo}", _linea(op))
            )
        return fila, ""
    java, motivo = expresion(valor, meseta.filas, meseta.tipos)
    if java is None:
        armado.pendientes.append(
            PendienteMigracion(SIN_TRADUCIR, f"columna '{destino}': {motivo}", _linea(op))
        )
    return java, motivo or ""


def _fila_de_columna(meseta: _Meseta, valor: str) -> tuple[str | None, str]:
    """`ventas.id_venta` o `id_venta` a `row1.id_venta`, según la entrada que tenga la columna."""
    tabla, columna = _tabla(valor)
    if tabla:
        for indice, fuente in enumerate(meseta.fuentes):
            if fuente.tabla == tabla:
                return f"{meseta.fila(indice)}.{columna}", ""
        return None, f"la tabla '{tabla}' no es una entrada del mapa"
    candidatas = [
        indice
        for indice, fuente in enumerate(meseta.fuentes)
        if any(propia.nombre == columna for propia in fuente.columnas)
    ]
    if len(candidatas) == 1:
        return f"{meseta.fila(candidatas[0])}.{columna}", ""
    if not candidatas:
        return None, f"la columna '{columna}' no está en ninguna entrada del mapa"
    return None, f"la columna '{columna}' está en varias entradas y el SAS no dice de cuál"


def _salidas(meseta: _Meseta, op: Operator, armado: Armado) -> list[SalidaMap]:
    """Salidas del `tMap`: las asignaciones del `SELECT` y, si hay, el `WHERE` como filtro."""
    filtro = _filtro(meseta, op, armado)
    derivaciones = _pasos(op, "derive")
    asignaciones = derivaciones[-1].get("assignments", []) if derivaciones else []
    if not asignaciones:
        principal = meseta.fuentes[0]
        return [
            SalidaMap(
                "out1",
                list(principal.columnas),
                {c.nombre: f"{PRINCIPAL}.{c.nombre}" for c in principal.columnas},
                filtro=filtro,
            )
        ]
    columnas: list[Columna] = []
    expresiones: dict[str, str] = {}
    for asignacion in asignaciones:
        destino = str(asignacion.get("target", "")).strip()
        if not destino or not str(asignacion.get("expression", "")).strip():
            continue
        java, _ = _valor(meseta, asignacion, armado, op)
        if java is None:
            continue
        fila, _, nombre = java.partition(".")
        tipo = meseta.tipo_de(fila, nombre) if fila.startswith("row") else "id_String"
        columnas.append(Columna(destino, tipo))
        expresiones[destino] = java
    if not columnas:
        return []
    return [SalidaMap("out1", columnas, expresiones, filtro=filtro)]


def construir(
    op: Operator,
    fuentes: list[Fuente],
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
) -> Armado:
    """`tMap` del operador `map` con sus entradas, llaves, expresiones y filtro."""
    armado = Armado()
    if not fuentes:
        armado.pendientes.append(
            PendienteMigracion(
                NO_SOPORTADO, "el mapa no tiene ninguna entrada demostrable", _linea(op)
            )
        )
        return armado
    uniones = _pasos(op, "join")
    join = uniones[-1] if uniones else None
    principal = _principal(fuentes, join)
    ordenadas = [fuentes[principal], *(f for i, f in enumerate(fuentes) if i != principal)]
    meseta = _Meseta(ordenadas)
    armado.entradas = {fuente.origen: meseta.fila(i) for i, fuente in enumerate(ordenadas)}
    for paso in ("aggregate",):
        if _pasos(op, paso):
            armado.pendientes.append(
                PendienteMigracion(
                    NO_SOPORTADO, f"el paso '{paso}' no tiene equivalente en el tMap", _linea(op)
                )
            )
    entradas = _entradas(meseta, join, armado, op)
    salidas = _salidas(meseta, op, armado)
    if not salidas:
        armado.pendientes.append(
            PendienteMigracion(
                NO_SOPORTADO, "el mapa no produce ninguna columna demostrable", _linea(op)
            )
        )
        return armado
    armado.columnas = list(salidas[0].columnas)
    try:
        armado.nodo = tmap(unico, entradas, salidas, x, y, ruta_java)
    except Exception as error:  # noqa: BLE001 — un mapa roto no se lleva el resto del Job
        armado.pendientes.append(
            PendienteMigracion(
                FALLO, f"tMap: {type(error).__name__}: {error}", _linea(op)
            )
        )
    return armado


__all__ = ["FALLO", "NO_SOPORTADO", "PRINCIPAL", "Armado", "Fuente", "construir"]
