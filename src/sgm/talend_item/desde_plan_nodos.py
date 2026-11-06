"""Nodos de lectura y escritura del Job, desde los operadores `read_file` y `write_file`.

El componente lo decide la pasada 10 y aquí no se vuelve a decidir: se toma `op.component["name"]`.
Lo que el SAS sí demuestra —ruta, formato, separador, cabecera y hoja— se escribe; lo que no
demuestra no se inventa, se deja como pendiente con su código y la línea del programa.

Los valores por omisión del separador son los del manual de SAS, no una suposición: `DBMS=CSV` es
coma, `DLM` es un blanco y `TAB` es tabulador (`docs/referencia/sas/proc.txt`, tabla 23.1 y el
apartado de `DELIMITER`). Un `DBMS` fuera de esa tabla no tiene separador demostrado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.ir.models import Column, Operator
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.plantillas import disponibles, nodo_desde_plantilla

# Tipo de la IR (`Column.type`) al tipo de Talend. Sin tipo demostrado, texto: es el único que no
# pierde información al escribir, y la pérdida de precisión se avisa en el pendiente del esquema.
TIPOS = {
    "String": "id_String",
    "Integer": "id_Integer",
    "Long": "id_Long",
    "Double": "id_Double",
    "Float": "id_Float",
    "BigDecimal": "id_BigDecimal",
    "Boolean": "id_Boolean",
    "Date": "id_Date",
}
# Separador por omisión de cada `DBMS` de SAS, con la extensión que documenta la tabla 23.1.
SEPARADORES = {"csv": ",", "dlm": " ", "tab": "\t"}
DELIMITADOS = frozenset(SEPARADORES)
EXCEL = frozenset({"xlsx", "xls"})


@dataclass
class Resultado:
    """Lo que sale de traducir un operador de archivo: su nodo y lo que no se pudo demostrar."""

    nodo: Nodo | None = None
    columnas: list[Columna] = field(default_factory=list)
    pendientes: list[PendienteMigracion] = field(default_factory=list)


def tipo_talend(tipo: str | None) -> str:
    return TIPOS.get(tipo or "", "id_String")


def columnas_talend(columnas: list[Column]) -> list[Columna]:
    """Columnas de la IR a columnas de Talend, conservando el orden del archivo."""
    return [Columna(columna.name, tipo_talend(columna.type)) for columna in columnas]


def ruta(literal: str | None) -> str:
    """Ruta de un literal de SAS (`'/data/x.csv'` o `"/data/x.csv"`) sin las comillas."""
    texto = (literal or "").strip()
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in "\"'":
        return texto[1:-1]
    return texto


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def separador(dbms: str | None, delimiter: str | None) -> tuple[str | None, str | None]:
    """Separador demostrado y, si no lo hay, el motivo.

    `DELIMITER` manda; si no está, el valor documentado del `DBMS`. Un `DBMS` desconocido sin
    `DELIMITER` no tiene separador: adivinarlo cambiaría todas las columnas del archivo.
    """
    if delimiter:
        return delimiter, None
    conocido = SEPARADORES.get((dbms or "").lower())
    if conocido is not None:
        return conocido, None
    return None, (
        f"DBMS={dbms or '(sin DBMS)'} sin DELIMITER: el SAS no dice con qué se separan las columnas"
    )


def _cabecera(getnames: bool | None) -> str:
    """`HEADER` de Studio: las líneas de cabecera que se saltan antes de la primera fila."""
    return "1" if getnames else "0"


def nodo_lectura(
    op: Operator,
    esquema: list[Column],
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
) -> Resultado:
    """`read_file` como `tFileInputDelimited` o `tFileInputExcel`."""
    params = op.params
    dbms = (params.get("dbms") or "").lower()
    columnas = columnas_talend(esquema)
    resultado = Resultado(columnas=columnas)
    archivo = ruta(params.get("datafile"))
    if dbms in EXCEL:
        guessingrows = params.get("guessingrows")
        if guessingrows is not None:
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-GUESSINGROWS",
                    f"{archivo}: GUESSINGROWS={guessingrows} se limita a archivos delimitados "
                    "según la referencia SAS; no se aplica a este Excel.",
                    _linea(op),
                )
            )
        if params.get("sheet") is None:
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-HOJA",
                    f"{archivo}: DBMS={dbms} sin SHEET; el SAS lee la primera hoja por omisión",
                    _linea(op),
                )
            )
        celdas: tuple[tuple[str, str], ...] = (("USE_REGEX", "false"),)
        if params.get("sheet") is not None:
            celdas = (("SHEETNAME", java(str(params["sheet"]))), *celdas)
        resultado.nodo = nodo_desde_plantilla(
            "tFileInputExcel",
            unico,
            x,
            y,
            {
                "FILENAME": archivo,
                "VERSION_2007": "true" if dbms == "xlsx" else "false",
                "HEADER": _cabecera(params.get("getnames")),
            },
            {"SHEETLIST": celdas},
            columnas,
            ruta_java,
        )
        return resultado
    guessingrows = params.get("guessingrows")
    if guessingrows is not None:
        resultado.pendientes.append(
            PendienteMigracion(
                "P-GUESSINGROWS",
                f"{archivo}: GUESSINGROWS={guessingrows} afecta la inferencia SAS de tipo y "
                "longitud; "
                "Talend requiere tipos explícitos, hay que validar el esquema emitido.",
                _linea(op),
            )
        )
    if dbms not in DELIMITADOS:
        resultado.pendientes.append(
            PendienteMigracion(
                "P-FORMATO-SIN-SOPORTE",
                f"{archivo}: DBMS={dbms or '(sin DBMS)'} no es un archivo delimitado ni de Excel",
                _linea(op),
            )
        )
        return resultado
    separa, motivo = separador(dbms, params.get("delimiter"))
    if separa is None:
        resultado.pendientes.append(
            PendienteMigracion("P-DELIMITADOR", f"{archivo}: {motivo}", _linea(op))
        )
        separa = SEPARADORES["csv"]  # el de la plantilla; queda dicho en el pendiente
    resultado.nodo = nodo_desde_plantilla(
        "tFileInputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": archivo,
            "FIELDSEPARATOR": java(separa),
            "HEADER": _cabecera(params.get("getnames")),
        },
        columnas=columnas,
        ruta_java=ruta_java,
    )
    return resultado


def nodo_escritura(
    op: Operator,
    columnas: list[Columna],
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
) -> Resultado:
    """`write_file` como `tFileOutputDelimited` o `tFileOutputExcel` si hay plantilla."""
    params = op.params
    dbms = (params.get("dbms") or "").lower()
    resultado = Resultado(columnas=list(columnas))
    archivo = ruta(params.get("outfile"))
    if dbms in EXCEL:
        if "tFileOutputExcel" not in disponibles():
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-COMPONENTE-SIN-PLANTILLA",
                    f"{archivo}: falta la plantilla de tFileOutputExcel, extraída de un Job real",
                    _linea(op),
                )
            )
            return resultado
        resultado.nodo = nodo_desde_plantilla(
            "tFileOutputExcel",
            unico,
            x,
            y,
            {"FILENAME": archivo},
            columnas=list(columnas),
            ruta_java=ruta_java,
        )
        return resultado
    separa, motivo = separador(dbms, params.get("delimiter"))
    if dbms not in DELIMITADOS:
        resultado.pendientes.append(
            PendienteMigracion(
                "P-FORMATO-SIN-SOPORTE",
                f"{archivo}: DBMS={dbms or '(sin DBMS)'} no es un archivo delimitado",
                _linea(op),
            )
        )
        return resultado
    if separa is None:
        resultado.pendientes.append(
            PendienteMigracion("P-DELIMITADOR", f"{archivo}: {motivo}", _linea(op))
        )
        separa = SEPARADORES["csv"]
    resultado.nodo = nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": archivo,
            "FIELDSEPARATOR": java(separa),
            "INCLUDEHEADER": "true",
            "APPEND": "false",
        },
        columnas=list(columnas),
        ruta_java=ruta_java,
    )
    return resultado


__all__ = [
    "DELIMITADOS",
    "EXCEL",
    "SEPARADORES",
    "TIPOS",
    "Resultado",
    "columnas_talend",
    "nodo_escritura",
    "nodo_lectura",
    "ruta",
    "separador",
    "tipo_talend",
]
