"""Casos L6 para procedimientos con efectos laterales y alcance de biblioteca explícito."""

URL_PROC = (
    "https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/docsets/proc/"
    "content/proc.pdf?locale=en"
)


def _copiar_ventas(entradas: dict[str, list[dict]]) -> list[dict]:
    """La salida esperada conserva filas de la entrada; los PROC bajo prueba son diagnósticos."""
    return [dict(fila) for fila in entradas["VENTAS"]]


ESPECIFICACIONES_L6_PROCS: dict[str, dict] = {
    "l6_63_limpieza_work": {
        "construcciones": [
            "PROC IMPORT",
            "PROC CONTENTS",
            "PROC DELETE",
            "PROC DATASETS DELETE",
            "WORK EXPLÍCITO",
        ],
        "entradas": {"VENTAS": (["id", "monto"], [(1, 10), (2, 40)])},
        "calculo": _copiar_ventas,
        "columnas": ["id", "monto"],
        "salida": "SALIDA",
        "programa": (
            "PROC IMPORT DATAFILE='.../entradas/VENTAS.csv' "
            "OUT=WORK.VENTAS DBMS=CSV REPLACE;\n"
            "GETNAMES=YES;\nRUN;\n"
            "DATA WORK.tmp;\n  SET WORK.ventas;\nRUN;\n"
            "PROC CONTENTS DATA=WORK.tmp;\nRUN;\n"
            "PROC DELETE DATA=WORK.tmp;\nRUN;\n"
            "DATA WORK.ventas2;\n  SET WORK.ventas;\nRUN;\n"
            "PROC DATASETS LIBRARY=WORK NOLIST;\n  DELETE ventas2;\nQUIT;\n"
            "DATA WORK.salida;\n  SET WORK.ventas;\nRUN;\n"
        ),
        "fuentes": [URL_PROC],
        "invariantes": ["filas(SALIDA) == 2", "suma(SALIDA.monto) == 50"],
        "razonamiento": (
            "PROC DELETE (proc.pdf, pp. 839, 847), PROC CONTENTS (pp. 541, 547) y PROC DATASETS "
            "(pp. 613, 627) afectan o describen miembros explícitos de WORK. El miembro ventas2 "
            "se crea antes de borrarlo. La salida esperada conserva las dos filas de VENTAS; no "
            "se infieren tipos de producción ni una salida de metadatos."
        ),
    },
}
