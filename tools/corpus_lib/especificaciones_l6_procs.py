"""Casos L6 para procedimientos con efectos laterales y alcance de biblioteca explícito."""

URL_PROC = (
    "https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/docsets/proc/"
    "content/proc.pdf?locale=en"
)


def _copiar_ventas(entradas: dict[str, list[dict]]) -> list[dict]:
    """La salida esperada conserva filas de la entrada; los PROC bajo prueba son diagnósticos."""
    return [dict(fila) for fila in entradas["VENTAS"]]


def _append_repetido(entradas: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Añade dos fuentes a la misma base y crea otra base con una fuente distinta."""
    acumulada = [
        *entradas["ACUM"],
        *entradas["N1"],
        *entradas["N2"],
    ]
    nueva = [dict(fila) for fila in entradas["N1"]]
    return {"ACUM": acumulada, "OTRA": nueva}


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
    "l6_64_append_repetido_y_base_nueva": {
        "construcciones": ["PROC APPEND", "BASE nueva", "BASE repetida"],
        "entradas": {
            "ACUM": (["id", "v"], [(1, "a"), (2, "b")]),
            "N1": (["id", "v"], [(3, "c")]),
            "N2": (["id", "v"], [(4, "d"), (5, "e")]),
        },
        "calculo_salidas": _append_repetido,
        "columnas": ["id", "v"],
        "salidas": ["ACUM", "OTRA"],
        "programa": (
            "PROC IMPORT DATAFILE='.../entradas/ACUM.csv' "
            "OUT=WORK.ACUM DBMS=CSV REPLACE;\nGETNAMES=YES;\nRUN;\n"
            "PROC IMPORT DATAFILE='.../entradas/N1.csv' "
            "OUT=WORK.N1 DBMS=CSV REPLACE;\nGETNAMES=YES;\nRUN;\n"
            "PROC IMPORT DATAFILE='.../entradas/N2.csv' "
            "OUT=WORK.N2 DBMS=CSV REPLACE;\nGETNAMES=YES;\nRUN;\n"
            "PROC APPEND BASE=WORK.ACUM DATA=WORK.N1;\nRUN;\n"
            "PROC APPEND BASE=WORK.ACUM DATA=WORK.N2;\nRUN;\n"
            "PROC APPEND BASE=WORK.OTRA DATA=WORK.N1;\nRUN;\n"
        ),
        "fuentes": [URL_PROC],
        "invariantes": ["filas(ACUM) == 5", "filas(OTRA) == 1"],
        "razonamiento": (
            "PROC APPEND agrega las observaciones de DATA al final de BASE (proc.pdf, p. 161). "
            "Cuando BASE no existe, SAS crea el conjunto y lo deja como el conjunto actual; el "
            "argumento DATA contiene las filas añadidas (proc.pdf, p. 639). Las llamadas repetidas "
            "se encadenan en el orden escrito. No se usan FORCE ni opciones adicionales."
        ),
    },
}
