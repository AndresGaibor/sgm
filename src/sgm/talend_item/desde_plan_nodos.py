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
from sgm.java_identificadores import is_java_identifier
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.desde_plan_nodos_escritura import nodo_escritura
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.motivo_entrada_data_step import motivo_entrada_data_step
from sgm.talend_item.plantillas import nodo_desde_plantilla

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
        quote = texto[0]
        return texto[1:-1].replace(quote + quote, quote)
    return texto


def _linea(op: Operator) -> int | None:
    linea_io = op.params.get("infile_line") or op.params.get("input_line")
    if isinstance(linea_io, int):
        return linea_io
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


def _cabecera(getnames: bool | int | None) -> str:
    """`HEADER` de Studio: las líneas de cabecera que se saltan antes de la primera fila."""
    if isinstance(getnames, int) and not isinstance(getnames, bool):
        return str(max(0, getnames))
    return "1" if getnames else "0"


def nodo_lectura(
    op: Operator,
    esquema: list[Column],
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
) -> Resultado:
    """`read_file` como componente de archivo cuando la equivalencia está documentada."""
    params = op.params
    dbms = (params.get("dbms") or "").lower()
    file_format = str(params.get("file_format") or "").lower()
    columnas = columnas_talend(esquema)
    resultado = Resultado(columnas=columnas)
    archivo = ruta(params.get("datafile"))
    if any(not is_java_identifier(columna.nombre) for columna in columnas):
        resultado.pendientes.append(
            PendienteMigracion(
                "P-ESQUEMA-NO-PORTABLE",
                "la lectura tiene nombres de columna no portables para Java",
                _linea(op),
            )
        )
        return resultado
    if file_format == "positional":
        if params.get("input_mode") == "formatted":
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-INFORMAT-SIN-SOPORTE",
                    f"{archivo or params.get('fileref') or '(sin ruta)'}: se conserva el INPUT "
                    "con informat, pero falta traducir sus máscaras y conversión de tipo.",
                    _linea(op),
                )
            )
        resultado.pendientes.append(
            PendienteMigracion(
                "P-COMPONENTE-SIN-PLANTILLA",
                f"{archivo or params.get('fileref') or '(sin ruta)'}: falta una plantilla real "
                "de tFileInputPositional y validar la disposición de columnas en Studio.",
                _linea(op),
            )
        )
        return resultado
    if file_format == "datalines":
        resultado.pendientes.append(
            PendienteMigracion(
                "P-DATALINES-SIN-LECTOR",
                "DATA step con DATALINES requiere conservar y emitir sus filas de entrada.",
                _linea(op),
            )
        )
        return resultado
    if file_format and file_format != "delimited" and file_format not in EXCEL:
        resultado.pendientes.append(
            PendienteMigracion(
                "P-FORMATO-SIN-SOPORTE",
                f"{archivo or params.get('fileref') or '(sin ruta)'}: formato SAS "
                f"'{file_format}' no tiene un lector verificado.",
                _linea(op),
            )
        )
        return resultado
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
                "FILENAME": java(archivo),
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
    data_step_input = "infile_statement" in params or "input_statement" in params
    if data_step_input and file_format != "delimited":
        resultado.pendientes.append(
            PendienteMigracion(
                "P-FORMATO-SIN-SOPORTE",
                f"{archivo or params.get('fileref') or '(sin ruta)'}: la sintaxis INFILE/INPUT "
                "no demuestra un formato delimitado compatible.",
                _linea(op),
            )
        )
        return resultado
    if data_step_input:
        pending_reason = motivo_entrada_data_step(params)
        if pending_reason:
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-INFILE-SIN-EQUIVALENCIA",
                    f"{archivo or params.get('fileref')}: {pending_reason}",
                    _linea(op),
                )
            )
            return resultado
        if not archivo:
            codigo = (
                "P-RUTA-DINAMICA"
                if params.get("source_dynamic")
                else "P-FILENAME-SIN-RESOLVER"
            )
            referencia = params.get("fileref") or "(sin referencia)"
            resultado.pendientes.append(
                PendienteMigracion(
                    codigo,
                    f"{referencia}: se necesita resolver la ruta SAS antes de generar la lectura.",
                    _linea(op),
                )
            )
            return resultado
    elif dbms not in DELIMITADOS:
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
        if data_step_input:
            resultado.pendientes.append(
                PendienteMigracion("P-DELIMITADOR", f"{archivo}: {motivo}", _linea(op))
            )
            return resultado
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
            "FILENAME": java(archivo),
            "FIELDSEPARATOR": java(separa),
            "HEADER": _cabecera(
                max(0, params["firstobs"] - 1)
                if data_step_input and isinstance(params.get("firstobs"), int)
                else params.get("getnames")
            ),
        },
        columnas=columnas,
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
