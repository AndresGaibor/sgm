"""Renderiza el programa SAS de un caso L4 generado desde vectores."""

from __future__ import annotations


def generar_programa(
    nombre: str,
    tabla: str,
    salida: str,
    asignacion: str,
    columnas: list[str],
    filas: list[tuple],
    numericas: tuple[str, ...],
) -> str:
    """Lee texto conservándolo como carácter y deja que PROC IMPORT infiera datos numéricos."""
    if numericas:
        lectura = (
            f"PROC IMPORT DATAFILE='.../entradas/{tabla}.csv' OUT=WORK.{tabla} "
            "DBMS=CSV REPLACE;\n"
            "  GETNAMES=YES;\n"
            "RUN;\n\n"
        )
    else:
        campos = []
        for indice, columna in enumerate(columnas):
            ancho = max(
                1,
                max(
                    (len(str(fila[indice])) for fila in filas if fila[indice] is not None),
                    default=0,
                ),
            )
            campos.append(f"{columna} : $CHAR{ancho}.")
        lectura = (
            f"DATA WORK.{tabla};\n"
            f"  INFILE '.../entradas/{tabla}.csv' DSD DLM=',' FIRSTOBS=2 TRUNCOVER;\n"
            f"  INPUT {' '.join(campos)};\n"
            "RUN;\n\n"
        )
    return (
        f"/* Caso {nombre}: vector de semántica SAS verificado por el oráculo. */\n"
        + lectura
        + f"DATA WORK.{salida};\n"
        + f"  SET WORK.{tabla};\n"
        + f"  {asignacion}\n"
        + "RUN;\n\n"
        + f"PROC EXPORT DATA=WORK.{salida} OUTFILE='.../salida/{salida}.csv'\n"
        + "  DBMS=CSV REPLACE;\n"
        + "RUN;\n"
    )
