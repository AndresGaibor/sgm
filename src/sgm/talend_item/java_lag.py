"""Código Java de `LAG` y `DIF` para un `tJavaRow` (lefunctionsref, pp. 1163-1164 y 663).

Cada aparición de `LAGn` tiene su cola, con `n` faltantes al empezar (p. 1164). La cola vive en
`globalMap` con nombre propio (`cola_<único>`): un `tJavaRow` no tiene campos de clase. Cuando la
función se ejecuta saca el valor más antiguo y guarda el actual. Con `IF`, las filas que no cumplen
la condición no tocan la cola y reciben faltante. `DIFn(x) = x - LAGn(x)` (p. 663).

Solo numérico: el valor de la cola es `Double`. Un `LAG` sobre texto queda pendiente.
"""

from __future__ import annotations

from sgm.java_identificadores import require_column_identifier


def codigo_lag(
    unico: str,
    destino: str,
    expresion: str,
    n: int,
    columnas: list[str],
    condicion: str | None = None,
    dif: bool = False,
) -> str:
    """Cuerpo de un `tJavaRow` que copia `columnas` y calcula `destino` como LAGn (o DIFn).

    `expresion` es Java que da `Double` sobre `input_row`; `condicion` es Java booleano, o None.
    """
    if n < 1:
        raise ValueError("LAG necesita un n mayor que cero")
    cola = f"cola_{require_column_identifier(unico)}"
    destino = require_column_identifier(destino)
    cabecera = [
        f'java.util.LinkedList<Double> {cola} = '
        f'(java.util.LinkedList<Double>) globalMap.get("{cola}");',
        f"if ({cola} == null) {{",
        f"    {cola} = new java.util.LinkedList<Double>();",
        f"    for (int i = 0; i < {n}; i++) {{ {cola}.add(null); }}",
        f'    globalMap.put("{cola}", {cola});',
        "}",
    ]
    copia = [
        f"output_row.{require_column_identifier(c)} = input_row.{require_column_identifier(c)};"
        for c in columnas
    ]
    valor = "(actual == null || previo == null) ? null : actual - previo" if dif else "previo"
    ejecucion = [
        f"Double actual = {expresion};",
        f"Double previo = {cola}.removeFirst();",
        f"{cola}.addLast(actual);",
        f"output_row.{destino} = {valor};",
    ]
    if condicion is None:
        return "\n".join(cabecera + copia + ejecucion)
    cuerpo = [f"    {linea}" for linea in ejecucion]
    return "\n".join(
        cabecera
        + copia
        + [f"if ({condicion}) {{", *cuerpo, "} else {", f"    output_row.{destino} = null;", "}"]
    )
