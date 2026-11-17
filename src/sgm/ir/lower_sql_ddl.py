"""CREATE TABLE ... LIKE de PROC SQL (plan C, C-12): una tabla vacía con las columnas de la otra.

El intérprete la trata como una lectura del origen que no deja filas y una escritura del molde. El
emisor de Talend no la traduce todavía: todo lo que crea la sentencia se marca `create_like`.
"""

from __future__ import annotations

from sgm.ir.builder import Builder


def lower_create_like(target: str, origen: str, ev, b: Builder) -> None:
    """Lectura de `origen`, filtro que no deja filas y escritura de `target`."""
    inicio = len(b.created)
    lectura = b.op("read", {"dataset": origen}, ev)
    filtro = b.op("filter", {"expression": "1 = 0"}, ev)
    escritura = b.op("write", {"dataset": target}, ev)
    b.link(lectura, filtro)
    b.link(filtro, escritura)
    for creado in b.created[inicio:]:
        creado.params["create_like"] = True
