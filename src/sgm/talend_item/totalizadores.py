"""Nodos de totales y de homologación que `job_producto` conecta a sus ramas.

Se separó de `jobs_producto.py` en el hito 87 para dejar sitio a los tres flujos de R1-04 sin
pasar el límite de 300 líneas de `AGENTS.md`. No cambia el comportamiento: son las mismas
funciones que el hito 84 usaba para el saldo y el `LEFT JOIN` del tipo de documento.
"""

from __future__ import annotations

from sgm.talend_item.arquitectura import ValidacionProducto
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.normalizacion import input_left_wd
from sgm.talend_item.plantillas import nodo_desde_plantilla


def a_decimal(
    columna: str, entrada: str = "row1", ancho: int = 20, decimales: int = 0
) -> str:
    """`input(left(col), w.d)`: la expresión verificada en el hito 83. Devuelve BigDecimal o null.

    El ancho por omisión (20) es el que este Job usaba antes de R1-02; cuando `cli_talend` aporta
    el informat demostrado por el SAS, se usa ese en su lugar.
    """
    return input_left_wd(f"{entrada}.{columna}", ancho, decimales)


def operaciones(
    con_saldo: bool, llave: str, conteo: str, suma: str
) -> tuple[tuple[str, str], ...]:
    """Operaciones del `tAggregateRow`: conteo por la llave y, si hay saldo, su suma."""
    resultado = [
        ("OUTPUT_COLUMN", conteo),
        ("FUNCTION", "count"),
        ("INPUT_COLUMN", llave),
        ("IGNORE_NULL", "false"),
    ]
    if con_saldo:
        resultado += [
            ("OUTPUT_COLUMN", suma),
            ("FUNCTION", "sum"),
            ("INPUT_COLUMN", "saldo"),
            ("IGNORE_NULL", "true"),
        ]
    return tuple(resultado)


def totales(
    unico: str,
    columnas: list[Columna],
    oper: tuple[tuple[str, str], ...],
    x: int,
    y: int,
    ruta_java: str | None,
) -> Nodo:
    return nodo_desde_plantilla(
        "tAggregateRow",
        unico,
        x,
        y,
        tablas={"OPERATIONS": oper},
        columnas=columnas,
        ruta_java=ruta_java,
    )


def homologacion(
    validacion: ValidacionProducto, x: int, y: int, ruta_java: str | None
) -> Nodo:
    """`tFileInputExcel` con la columna de homologación. El archivo lo elige el padre."""
    return nodo_desde_plantilla(
        "tFileInputExcel",
        "tFileInputExcel_1",
        x,
        y,
        {
            "FILENAME": "context.ruta_insumos + context.arch_hom_tipo_doc",
            # Vacío o "***" hacen que Studio no compile; el archivo no tiene clave.
            "PASSWORD": '"sgm_ref"',
        },
        {"SHEETLIST": (("SHEETNAME", "context.hoja_excel"), ("USE_REGEX", "false"))},
        [Columna(validacion.columna_lookup)],
        ruta_java,
    )


__all__ = ["a_decimal", "homologacion", "operaciones", "totales"]
