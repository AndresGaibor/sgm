"""Expresiones Java del `tMap` escritas desde el SAS, con la fila resuelta y el faltante cubierto.

El traductor de `sgm.expressions` devuelve Java con `input_row` como marcador de fila: no sabe de
qué entrada del `tMap` sale cada columna. Aquí se cambia por el nombre real de la conexión (`row1`
para la principal, `row2` en adelante para los lookups) usando el esquema de cada entrada.

Además se cubre el faltante, que es la diferencia de semántica que rompe el Job: en SAS un faltante
numérico es **menor que cualquier número** y en Java un `null` en una comparación lanza
`NullPointerException`. Una condición copiada tal cual cambia el resultado del programa o lo tumba.
La comprobación del faltante se reutiliza de `filtros_cuenta.faltante`, la misma de R1-06 y R1-07:
nulo, texto vacío o texto no numérico.
"""

from __future__ import annotations

import re

from sgm.expressions.expressions import translate
from sgm.talend_item.filtros_cuenta import faltante

# Columnas de Talend que son número: admiten comparación de orden directa.
NUMERICAS = frozenset(
    {"id_Integer", "id_Long", "id_Double", "id_Float", "id_BigDecimal", "id_Short", "id_Byte"}
)

_COLUMNA = re.compile(r"input_row\.(\w+)")
# Comparación de orden entre una columna y un literal numérico, tal como la escribe el traductor:
# `(row1.saldo < 500)`. Es la forma que se puede hacer segura sin adivinar nada.
_ORDEN_LITERAL = re.compile(r"\(([A-Za-z_][\w.]*)\s*(<=|>=|<|>)\s*(-?\d+(?:\.\d+)?)\)")
_OPERADOR_ORDEN = re.compile(r"<=|>=|<|>")


def resolver_filas(java: str, filas: dict[str, set[str]]) -> tuple[str | None, str | None]:
    """Cambia `input_row.col` por `rowN.col` según la única entrada que tiene esa columna.

    Devuelve `(expresión, None)` o `(None, motivo)`: una columna que no está en ninguna entrada, o
    que está en más de una, no se resuelve a ciegas.
    """
    usadas = _COLUMNA.findall(java)
    if not usadas:
        return java, None
    destino: dict[str, str] = {}
    for columna in dict.fromkeys(usadas):
        candidatas = [fila for fila, nombres in filas.items() if columna in nombres]
        if not candidatas:
            return None, f"la columna '{columna}' no está en ninguna entrada del mapa"
        if len(candidatas) > 1:
            return None, (
                f"la columna '{columna}' está en varias entradas "
                f"({', '.join(sorted(candidatas))}); el SAS no dice de cuál"
            )
        destino[columna] = candidatas[0]
    return _COLUMNA.sub(lambda m: f"{destino[m.group(1)]}.{m.group(1)}", java), None


def _segura(columna: str, operador: str, literal: str, tipos: dict[str, str]) -> str:
    """Comparación de orden con el faltante tratado como en SAS.

    `<` y `<=` son verdaderos con faltante (es menor que cualquier número); `>` y `>=` son falsos.
    Sobre una columna de texto se comprueba primero que el texto sea numérico, como hace el `input`
    del SAS: lo que no lo es, es faltante.
    """
    tipo = tipos.get(columna)
    if tipo in NUMERICAS:
        guarda = f"{columna} == null" if operador in ("<", "<=") else f"{columna} != null"
        union = "||" if operador in ("<", "<=") else "&&"
        return f"({guarda} {union} {columna} {operador} {literal})"
    fila, _, nombre = columna.rpartition(".")
    sin_numero = faltante(nombre, fila)
    valor = f"java.lang.Double.parseDouble({columna})"
    if operador in ("<", "<="):
        return f"({sin_numero} || {valor} {operador} {literal})"
    return f"(!{sin_numero} && {valor} {operador} {literal})"


def cubrir_faltante(java: str, tipos: dict[str, str]) -> tuple[str | None, str | None]:
    """Hace seguras las comparaciones de orden de una expresión Java ya traducida.

    Solo se tocan las comparaciones de columna contra literal numérico. Si queda alguna otra
    comparación de orden, no se puede demostrar su semántica con faltantes y se devuelve el motivo.
    """
    partes: list[str] = []
    ultimo = 0
    for encontrada in _ORDEN_LITERAL.finditer(java):
        partes.append(java[ultimo : encontrada.start()])
        columna, operador, literal = encontrada.groups()
        partes.append(_segura(columna, operador, literal, tipos))
        ultimo = encontrada.end()
    partes.append(java[ultimo:])
    # Lo que quedó fuera de las comparaciones cubiertas: si tiene un orden, no está demostrado.
    resto = _ORDEN_LITERAL.sub(" ", java)
    sobrante = _OPERADOR_ORDEN.search(resto)
    if sobrante is not None:
        inicio = max(0, sobrante.start() - 40)
        return None, (
            "comparación de orden sin semántica de faltante demostrada: "
            f"{' '.join(resto[inicio:][:80].split())}"
        )
    return "".join(partes), None


def expresion(
    sas: str, filas: dict[str, set[str]], tipos: dict[str, str]
) -> tuple[str | None, str | None]:
    """Java de una expresión o condición del SAS, con la fila resuelta y el faltante cubierto."""
    traduccion = translate(sas)
    if traduccion.talend is None:
        motivo = "; ".join(traduccion.warnings) or "el traductor no la reconoce"
        return None, motivo
    resuelta, motivo = resolver_filas(traduccion.talend, filas)
    if resuelta is None:
        return None, motivo
    return cubrir_faltante(resuelta, tipos)


__all__ = ["NUMERICAS", "cubrir_faltante", "expresion", "resolver_filas"]
