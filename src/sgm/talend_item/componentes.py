"""Componentes de Talend con su cabecera y parámetros tal como los guarda Studio 8.0.1.

Cada constructor copia los parámetros de un nodo real guardado por Studio. Solo se añaden los
componentes que se han comparado contra un Job real (ver `tests/unit/test_talend_item.py`).
"""

from __future__ import annotations

from sgm.talend_item.modelo import Columna, Fila, Nodo, Tabla


def _cabecera(
    componente: str,
    unico: str,
    version: str,
    familia: str,
    ayuda: str | None = None,
    inicio: bool = False,
    final: bool = False,
    ruta_java: str = "",
) -> list[Fila | Tabla]:
    """Parámetros comunes del principio de todo nodo."""
    filas: list[Fila | Tabla] = [
        ("TEXT", "UNIQUE_NAME", unico, "false"),
        ("TEXT", "COMPONENT_NAME", componente, "false"),
        ("TEXT", "VERSION", f"{version} (ALPHA)", "false"),
        ("TEXT", "FAMILY", familia, "false"),
    ]
    if inicio:
        filas.append(("CHECK", "START", "true", "false"))
    filas += [
        ("CHECK", "STARTABLE", str(inicio).lower(), "false"),
        ("CHECK", "SUBTREE_START", str(inicio).lower(), "false"),
        ("CHECK", "END_OF_FLOW", str(final).lower(), "false"),
        ("TEXT", "HELP", ayuda or f"org.talend.help.{componente}", "false"),
        ("DIRECTORY", "IREPORT_PATH", "", "false"),
        ("DIRECTORY", "JAVA_LIBRARY_PATH", ruta_java, "false"),
    ]
    return filas


def _texto(valor: str) -> str:
    """Literal de cadena de Java para un parámetro de Talend."""
    escapado = valor.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return '"' + escapado + '"'


def fixed_flow_input(
    unico: str,
    columnas: list[Columna],
    filas: list[list[str]],
    x: int = 0,
    y: int = 0,
    ruta_java: str = "",
) -> Nodo:
    """`tFixedFlowInput` con filas en tabla. Cada valor es una expresión de Java ya escrita."""
    refs = [c.nombre for c in columnas]
    primera = [(ref, valor) for ref, valor in zip(refs, filas[0], strict=True)] if filas else []
    valores: list[tuple[str, str]] = []
    for ref, valor in primera:
        valores += [("SCHEMA_COLUMN", ref), ("VALUE", valor)]
    intable = tuple((ref, valor) for fila in filas for ref, valor in zip(refs, fila, strict=True))
    parametros = _cabecera(
        "tFixedFlowInput", unico, "0.102", "Misc", inicio=True, ruta_java=ruta_java
    )
    parametros += [
        ("TEXT", "NB_ROWS", "1", None),
        ("RADIO", "USE_SINGLEMODE", "false", None),
        Tabla("VALUES", tuple(valores), show="false"),
        ("RADIO", "USE_INTABLE", "true", None),
        Tabla("INTABLE", intable),
        ("RADIO", "USE_INLINECONTENT", "false", None),
        ("TEXT", "ROWSEPARATOR", _texto("\n"), "false"),
        ("TEXT", "FIELDSEPARATOR", _texto(";"), "false"),
        ("MEMO", "INLINECONTENT", "", "false"),
    ]
    return Nodo("tFixedFlowInput", "0.102", unico, x, y, parametros, columnas=columnas)


def log_row(
    unico: str, columnas: list[Columna], x: int = 0, y: int = 0, ruta_java: str = ""
) -> Nodo:
    """`tLogRow` en modo básico, con separador `|`."""
    parametros = _cabecera(
        "tLogRow", unico, "0.101", "Logs_Errors", final=True, ruta_java=ruta_java
    )
    parametros += [
        ("RADIO", "BASIC_MODE", "true", None),
        ("RADIO", "TABLE_PRINT", "false", None),
        ("RADIO", "VERTICAL", "false", None),
        ("RADIO", "PRINT_UNIQUE", "true", "false"),
        ("RADIO", "PRINT_LABEL", "false", "false"),
        ("RADIO", "PRINT_UNIQUE_LABEL", "false", "false"),
        ("TEXT", "FIELDSEPARATOR", _texto("|"), None),
        ("CHECK", "PRINT_HEADER", "false", None),
        ("CHECK", "PRINT_UNIQUE_NAME", "false", None),
        ("CHECK", "PRINT_COLNAMES", "false", None),
        ("CHECK", "USE_FIXED_LENGTH", "false", None),
        Tabla(
            "LENGTHS",
            tuple(par for c in columnas for par in (("SCHEMA_COLUMN", c.nombre), ("LENGTH", "10"))),
            show="false",
        ),
        ("CHECK", "PRINT_CONTENT_WITH_LOG4J", "true", None),
        ("TEXT", "SCHEMA_OPT_NUM", "100", "false"),
    ]
    return Nodo("tLogRow", "0.101", unico, x, y, parametros, columnas=columnas)
