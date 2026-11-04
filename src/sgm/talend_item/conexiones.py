"""Conexiones de Talend distintas de la fila: disparadores, iteración y Run if.

Los `lineStyle` y los parámetros de cada una se copiaron de Jobs reales guardados por Studio 8.0.1.
`n` es el ordinal de la conexión de ese tipo en el Job: Studio lo suma al nombre (`OnSubjobOk2`).
"""

from __future__ import annotations

from sgm.talend_item.modelo import Conexion


def _disparador(
    origen: str, destino: str, n: int, conector: str, estilo: int, base: str
) -> Conexion:
    unico = f"{base}{n}"
    return Conexion(
        origen,
        destino,
        unico,
        conector,
        estilo,
        (("TEXT", "UNIQUE_NAME", unico, "false"),),
        etiqueta=base,
    )


def al_terminar_subjob(origen: str, destino: str, n: int = 1) -> Conexion:
    """`OnSubjobOk`: el destino corre cuando termina bien todo el subjob del origen."""
    return _disparador(origen, destino, n, "SUBJOB_OK", 1, "OnSubjobOk")


def al_terminar_componente(origen: str, destino: str, n: int = 1) -> Conexion:
    """`OnComponentOk`: el destino corre cuando el origen termina bien."""
    return _disparador(origen, destino, n, "COMPONENT_OK", 3, "OnComponentOk")


def iterar(origen: str, destino: str, n: int = 1, paralelo: int = 0) -> Conexion:
    """`Iterate`: el destino corre una vez por cada iteración del origen."""
    unico = f"iterate{n}"
    parametros = (
        ("CHECK", "ENABLE_PARALLEL", str(paralelo > 0).lower(), None),
        ("TEXT", "NUMBER_PARALLEL", str(paralelo or 2), "false"),
        ("TEXT", "UNIQUE_NAME", unico, "false"),
    )
    return Conexion(origen, destino, unico, "ITERATE", 7, parametros, etiqueta="Iterate")


def si(origen: str, destino: str, condicion: str, n: int = 1) -> Conexion:
    """`Run if`: el destino corre si la condición de Java es verdadera."""
    unico = f"If{n}"
    parametros = (
        ("MEMO_JAVA", "CONDITION", condicion, None),
        ("CHECK", "ACTIVATE", "false", "false"),
        ("TEXT", "UNIQUE_NAME", unico, "false"),
    )
    return Conexion(origen, destino, unico, "RUN_IF", 6, parametros, etiqueta="If")
