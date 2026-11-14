"""Casos L4 de actualización parcial de una variable de texto."""

from __future__ import annotations

FUENTE = (
    "https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/"
    "docsets/lefunctionsref/content/lefunctionsref.pdf?locale=en"
)

_COLUMNAS = ["ID", "CODIGO"]
_FILAS = [(1, "ABCDEF"), (2, "GHIJKL")]
_PROGRAMA = """/* Caso l4_150_substr_pseudovariable: sustitución en DATA step. */
PROC IMPORT DATAFILE='.../entradas/CODIGOS.csv' OUT=WORK.CODIGOS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.CODIGOS_FIX;
  LENGTH CODIGO $6;
  SET WORK.CODIGOS;
  SUBSTR(CODIGO, 2, 3) = 'XY';
RUN;

PROC EXPORT DATA=WORK.CODIGOS_FIX OUTFILE='.../salida/CODIGOS_FIX.csv' DBMS=CSV REPLACE;
RUN;
"""

ESPECIFICACIONES_L4C = {
    "l4_150_substr_pseudovariable": {
        "construcciones": ["DATA STEP", "SUBSTR (left of =)"],
        "entrada": ("CODIGOS", _COLUMNAS, _FILAS, ("ID",)),
        "asignaciones": [
            (
                "CODIGO",
                "CODIGO",
                (("substr_asignar", 2, 3, "XY"),),
                "SUBSTR(CODIGO, 2, 3) = 'XY';",
            )
        ],
        "salida": "CODIGOS_FIX",
        "fuentes": [FUENTE],
        "invariantes": ["filas(CODIGOS_FIX) == 2"],
        "razonamiento": (
            "SUBSTR a la izquierda reemplaza tres caracteres, rellena el valor corto con blanco "
            "y conserva los caracteres restantes; salida calculada por el oráculo substr_asignar."
        ),
        "programa": _PROGRAMA,
    }
}

