"""Semántica SAS de cabeceras e inferencia al leer archivos delimitados."""

from __future__ import annotations

from sgm.ir.models import Column
from sgm.migrar.esquemas import PendienteMigracion
from sgm.migrar.tipos_import import nombres_por_omision


def lineas_a_saltar(getnames: bool, datarow: int | None) -> int:
    """Convierte la fila inicial de SAS en líneas previas a saltar en Talend."""
    if datarow is None:
        return 1 if getnames else 0
    if isinstance(datarow, bool) or not isinstance(datarow, int):
        raise ValueError("DATAROW debe ser un entero literal; proc.pdf, p. 1385")
    minimo = 2 if getnames else 1
    if datarow < minimo:
        raise ValueError(
            f"DATAROW={datarow} no es válido con GETNAMES={'YES' if getnames else 'NO'}; "
            "proc.pdf, p. 1385"
        )
    return datarow - 1


def aviso_guessingrows(
    esquema: list[Column],
    guessingrows: object,
    linea: int | None,
    *,
    datarow: int | None = None,
    getnames: bool = True,
) -> PendienteMigracion | None:
    """Solo bloquea la lectura si GUESSINGROWS aún es necesario para fijar algún tipo."""
    if guessingrows is None and datarow is None:
        return None
    limite = 20 if guessingrows is None else guessingrows
    valor = "20 (valor por omisión)" if guessingrows is None else str(guessingrows)
    fila_datos = datarow if datarow is not None else (2 if getnames else 1)
    if isinstance(limite, int) and not isinstance(limite, bool):
        if limite <= fila_datos:
            return PendienteMigracion(
                "P-GUESSINGROWS",
                f"GUESSINGROWS={valor} debe ser mayor que DATAROW={fila_datos} "
                "(proc.pdf, p. 1388).",
                linea,
            )
    if guessingrows is None:
        return None
    todos_tipados = bool(esquema) and all(columna.type is not None for columna in esquema)
    if todos_tipados:
        return PendienteMigracion(
            "A-GUESSINGROWS-TIPOS-FIJADOS",
            f"GUESSINGROWS={valor}: todos los tipos ya están fijados; Talend no ejecuta "
            "la inferencia de SAS al leer el archivo.",
            linea,
        )
    return PendienteMigracion(
        "P-GUESSINGROWS",
        f"GUESSINGROWS={valor} afecta la inferencia SAS de tipo y longitud; falta demostrar "
        "el tipo de todas las columnas y no se emite una lectura parcial.",
        linea,
    )


__all__ = ["aviso_guessingrows", "lineas_a_saltar", "nombres_por_omision"]
