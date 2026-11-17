"""Casos L6 para procedimientos con efectos laterales y alcance de biblioteca explícito."""

from .referencia_datastep import proc_sort, proc_sort_noduprec_por_llave

URL_PROC = (
    "https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/docsets/proc/"
    "content/proc.pdf?locale=en"
)
URL_LRCON = (
    "https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/docsets/lrcon/"
    "content/lrcon.pdf?locale=en"
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


def _nodupkey_dupout(entradas: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Conserva la primera fila por llave y devuelve el resto como salida duplicada."""
    ordenadas = proc_sort(entradas["R"], ["id"])
    vistas: set[tuple] = set()
    unicas: list[dict] = []
    duplicadas: list[dict] = []
    for fila in ordenadas:
        llave = (fila["id"],)
        if llave in vistas:
            duplicadas.append(fila)
        else:
            vistas.add(llave)
            unicas.append(fila)
    return {"U": unicas, "D": duplicadas}


ESPECIFICACIONES_L6_PROCS: dict[str, dict] = {
    "l6_60_noduprec_por_llave": {
        "construcciones": ["PROC SORT", "NODUPREC", "BY PARCIAL"],
        "entradas": {
            "R": (["id", "v"], [(1, "a"), (1, "b"), (1, "a"), (2, "c")]),
        },
        "calculo": lambda entradas: proc_sort_noduprec_por_llave(entradas["R"], ["id"]),
        "columnas": ["id", "v"],
        "salida": "R_SIN",
        "programa": (
            "PROC IMPORT DATAFILE='.../entradas/R.csv' OUT=WORK.R DBMS=CSV REPLACE;\n"
            "GETNAMES=YES;\nRUN;\n"
            "PROC SORT DATA=WORK.R OUT=WORK.R_SIN NODUPREC; BY id; RUN;\n"
        ),
        "fuentes": [URL_LRCON, URL_PROC],
        "invariantes": ["filas(R_SIN) == 4"],
        "estado": "revisado",
        "motivo": "El caso limita la traducción a las filas cuya adyacencia se demuestra.",
        "razonamiento": (
            "El sort indicator identifica con NODUPREC la propiedad de no tener observaciones "
            "duplicadas adyacentes (lrcon.pdf, p. 714). Con BY id, la segunda fila distinta "
            "mantiene separadas las dos observaciones (1,a); no se deben tratar como DISTINCT. "
            "El lowering conserva el orden y deja P-NODUPREC-NO-ADYACENTE para llaves parciales."
        ),
    },
    "l6_61_nodupkey_dupout": {
        "construcciones": ["PROC SORT", "NODUPKEY", "DUPOUT", "EQUALS"],
        "entradas": {
            "R": (["id", "v"], [(2, "x"), (1, "a"), (2, "y"), (1, "b")]),
        },
        "calculo_salidas": _nodupkey_dupout,
        "columnas": ["id", "v"],
        "salidas": ["U", "D"],
        "programa": (
            "PROC IMPORT DATAFILE='.../entradas/R.csv' OUT=WORK.R DBMS=CSV REPLACE;\n"
            "GETNAMES=YES;\nRUN;\n"
            "PROC SORT DATA=WORK.R OUT=WORK.U NODUPKEY DUPOUT=WORK.D; BY id; RUN;\n"
        ),
        "fuentes": [URL_PROC],
        "invariantes": ["filas(U) == 2", "filas(D) == 2"],
        "estado": "revisado",
        "motivo": "DUPOUT y EQUALS contrastados con la guía de PROC SORT.",
        "razonamiento": (
            "DUPOUT= guarda las observaciones duplicadas que se eliminan (proc.pdf, p. 2461); "
            "con NODUPKEY es una salida válida. EQUALS conserva el orden relativo de entrada "
            "dentro de cada llave y es el valor predeterminado (proc.pdf, p. 2471)."
        ),
    },
    "l6_62_sort_descending_noequals": {
        "construcciones": ["PROC SORT", "DESCENDING", "NOEQUALS"],
        "entradas": {
            "R": (["id", "v"], [(1, "a"), (3, "c"), (2, "b"), (3, "d")]),
        },
        "calculo": lambda entradas: proc_sort(entradas["R"], ["id"], descending=[True]),
        "columnas": ["id", "v"],
        "salida": "S",
        "programa": (
            "PROC IMPORT DATAFILE='.../entradas/R.csv' OUT=WORK.R DBMS=CSV REPLACE;\n"
            "GETNAMES=YES;\nRUN;\n"
            "PROC SORT DATA=WORK.R OUT=WORK.S NOEQUALS; BY DESCENDING id; RUN;\n"
        ),
        "fuentes": [URL_PROC],
        "invariantes": ["filas(S) == 4"],
        "estado": "revisado",
        "motivo": "El sentido de BY y el orden no garantizado de NOEQUALS están documentados.",
        "orden_relevante": False,
        "orden_grupo": [{"columna": "id", "descendente": True}],
        "razonamiento": (
            "DESCENDING aplica el orden inverso a la variable BY siguiente (proc.pdf, p. 2479). "
            "NOEQUALS no preserva necesariamente el orden de observaciones con la misma llave "
            "y puede variar entre ejecuciones (proc.pdf, p. 2471); se compara el orden de grupos, "
            "no el orden interno de id=3."
        ),
    },
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
