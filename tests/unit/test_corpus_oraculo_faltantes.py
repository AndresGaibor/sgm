"""Pruebas del oráculo SQL: faltantes de texto, ROUND, NE, OUTER UNION CORR, OBS= e INTO.

Cada construcción se comprueba con la forma traducida y con el resultado al ejecutarla sobre tablas
pequeñas. Los vectores de `tests/corpus/semantica/vectores.yaml` (`cmp-texto-01`, `ismissing-02`,
`round-05`, `round-06`) son la referencia de SAS. Va aparte de `test_corpus_oraculo_sql.py` para no
pasar de 300 líneas.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.csv_tabla import Tabla  # noqa: E402
from corpus_lib.esquema_sql import Esquema  # noqa: E402
from corpus_lib.oraculo_sql import ejecutar_proc_sql  # noqa: E402
from corpus_lib.sas_texto import sentencias_proc_sql  # noqa: E402
from corpus_lib.traduccion_sql import NoSoportado, a_sqlite  # noqa: E402


def _ejecutar(sql_sas: str, tablas: dict[str, Tabla], salida: str = "r") -> list[tuple]:
    """Ejecuta un CREATE TABLE WORK.r AS SELECT de SAS sobre las tablas y devuelve las filas."""
    sentencias_sql = sentencias_proc_sql(f"PROC SQL;\n{sql_sas}\nQUIT;")
    return ejecutar_proc_sql(sentencias_sql, tablas, [salida])[salida].filas


def _sqlite(sql: str) -> object:
    """Ejecuta una expresión sin tablas y devuelve el primer valor."""
    return sqlite3.connect(":memory:").execute(sql).fetchone()[0]


TEXTOS = Tabla(
    ["id", "ciudad"],
    [(1, ""), (2, "   "), (3, None), (4, "Sur")],
    ["INTEGER", "TEXT"],
)
ESQUEMA_TEXTOS = Esquema({"t": [("id", "INTEGER"), ("ciudad", "TEXT")]})


# Faltantes de texto (tarea 1 del hito 75c).


def test_texto_vacio_o_en_blanco_es_is_missing():
    filas = _ejecutar("CREATE TABLE WORK.r AS SELECT id FROM T WHERE ciudad IS MISSING;", {"T": TEXTOS})
    assert [fila[0] for fila in filas] == [1, 2, 3]


def test_texto_vacio_es_igual_a_cadena_vacia():
    filas = _ejecutar("CREATE TABLE WORK.r AS SELECT id FROM T WHERE ciudad = '';", {"T": TEXTOS})
    assert [fila[0] for fila in filas] == [1, 2]


def test_is_missing_tras_left_join_cubre_el_null_del_lado_derecho():
    # Caso 02: el LEFT JOIN deja NULL en una columna de texto; también es faltante.
    izquierda = Tabla(["id"], [(1,), (2,), (3,)], ["INTEGER"])
    derecha = Tabla(["nro", "marca"], [(1, "x")], ["INTEGER", "TEXT"])
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT a.id FROM I a LEFT JOIN D d ON (a.id = d.nro) "
        "WHERE d.marca IS MISSING;",
        {"I": izquierda, "D": derecha},
    )
    assert [fila[0] for fila in filas] == [2, 3]


def test_comparacion_de_texto_ignora_blancos_finales_del_campo():
    # Vector cmp-texto-01: 'fox ' = 'fox' es verdadero en SAS.
    tabla = Tabla(["id", "sigla"], [(1, "fox "), (2, "fox"), (3, " fox")], ["INTEGER", "TEXT"])
    filas = _ejecutar("CREATE TABLE WORK.r AS SELECT id FROM T WHERE sigla = 'fox';", {"T": tabla})
    assert [fila[0] for fila in filas] == [1, 2]


def test_join_de_texto_ignora_blancos_finales():
    izquierda = Tabla(["clave"], [("CC ",), ("AB",)], ["TEXT"])
    derecha = Tabla(["clave", "n"], [("CC", 1), ("AB", 2)], ["TEXT", "INTEGER"])
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT i.clave, d.n FROM I i INNER JOIN D d ON (i.clave = d.clave);",
        {"I": izquierda, "D": derecha},
    )
    assert filas == [("CC ", 1), ("AB", 2)]


def test_coalesce_salta_el_texto_en_blanco():
    # En SAS COALESCE salta un blanco: devuelve el siguiente valor.
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT id, COALESCE(ciudad, 'X') AS c FROM T;", {"T": TEXTOS}
    )
    assert [fila[1] for fila in filas] == ["X", "X", "X", "Sur"]


def test_count_no_cuenta_el_texto_en_blanco():
    # Solo 'Sur' es un valor presente: '' y '   ' son faltantes, y el NULL también.
    filas = _ejecutar("CREATE TABLE WORK.r AS SELECT COUNT(ciudad) AS n FROM T;", {"T": TEXTOS})
    assert filas == [(1,)]


def test_is_missing_con_esquema_de_texto_en_la_traduccion():
    sql = a_sqlite("SELECT id FROM t WHERE ciudad IS MISSING", ESQUEMA_TEXTOS)
    assert sql == "SELECT id FROM t WHERE (ciudad IS NULL OR rtrim(ciudad) = '')"


# ROUND con unidad (tarea 2). Valores de SAS: vectores round-01 a round-06.


@pytest.mark.parametrize(
    ("sql_sas", "esperado"),
    [
        ("ROUND(1234.56789, 100)", 1200),       # round-01
        ("ROUND(1234.56789, 0.1)", 1234.6),     # round-02
        ("ROUND(1234.56789, 0.01)", 1234.57),   # round-03
        ("ROUND(1234.56789, 0.11111)", 1234.54321),  # round-04
        ("ROUND(2.5)", 3),                      # round-05
        ("ROUND(-2.5)", -3),                    # round-06
        ("ROUND(12.345, 0.01)", 12.35),         # SAS da 12.35 (ver DIFERENCIAS.md)
        ("ROUND(12.344, 0.01)", 12.34),
        ("ROUND(-12.345, 0.01)", -12.35),
        ("ROUND(7, 1)", 7),
    ],
)
def test_round_con_unidad_como_sas(sql_sas, esperado):
    assert _sqlite(a_sqlite(f"SELECT {sql_sas} AS r")) == pytest.approx(esperado, abs=1e-9)


def test_round_con_argumento_columna_y_anidado():
    tabla = Tabla(["x"], [(12.345,), (-2.5,)], ["REAL"])
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT ROUND(ROUND(x, 0.01), 0.1) AS r FROM T;", {"T": tabla}
    )
    assert [round(fila[0], 6) for fila in filas] == [12.4, -2.5]


def test_round_no_admite_mas_de_dos_argumentos():
    with pytest.raises(NoSoportado, match="ROUND"):
        a_sqlite("SELECT ROUND(1, 2, 3) AS r")


# NE, OBS= e INTO (tarea 3).


def test_ne_pasa_a_distinto():
    assert a_sqlite("SELECT id FROM t WHERE a NE 1") == "SELECT id FROM t WHERE a <> 1"


def test_obs_limita_las_filas_leidas_de_la_tabla():
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT id FROM T (OBS=2);", {"T": TEXTOS}
    )
    assert filas == [(1,), (2,)]


def test_obs_con_alias_y_en_subconsulta_escalar():
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT (SELECT COUNT(*) FROM T) AS total, x.id "
        "FROM T (OBS=1) x;",
        {"T": TEXTOS},
    )
    assert filas == [(4, 1)]


def test_into_sigue_no_soportado_con_mensaje_claro():
    with pytest.raises(NoSoportado, match="macrovariables"):
        a_sqlite("SELECT id INTO :m FROM t")


# OUTER UNION CORR (tarea 3).


def test_outer_union_corr_alinea_por_nombre_y_rellena_con_nulo():
    izquierda = Tabla(["id", "monto"], [(1, 10), (2, 20)], ["INTEGER", "INTEGER"])
    derecha = Tabla(["monto", "id", "extra"], [(30, 3, "z")], ["INTEGER", "INTEGER", "TEXT"])
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT * FROM I "
        "OUTER UNION CORR SELECT * FROM D;",
        {"I": izquierda, "D": derecha},
    )
    assert filas == [(1, 10, None), (2, 20, None), (3, 30, "z")]


def test_outer_union_corr_con_select_de_columnas_y_alias():
    izquierda = Tabla(["id", "n"], [(1, 5)], ["INTEGER", "INTEGER"])
    derecha = Tabla(["id"], [(2,)], ["INTEGER"])
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT i.id, n AS total FROM I i "
        "OUTER UNION CORR SELECT id FROM D;",
        {"I": izquierda, "D": derecha},
    )
    assert filas == [(1, 5), (2, None)]


def test_outer_union_corr_sin_nombre_de_columna_no_soportado():
    with pytest.raises(NoSoportado, match="sin nombre"):
        a_sqlite(
            "CREATE TABLE r AS SELECT id, monto * 2 FROM I OUTER UNION CORR SELECT id FROM D",
            Esquema({}),
        )


def test_outer_union_corr_encadenado_apila_los_tres_selects():
    # Caso 02 de L8/totales: tres SELECT seguidos; cada uno aporta sus columnas por nombre.
    a = Tabla(["id", "tipo"], [(1, "A")], ["INTEGER", "TEXT"])
    b = Tabla(["id", "gmf"], [(2, "B")], ["INTEGER", "TEXT"])
    c = Tabla(["id"], [(3,)], ["INTEGER"])
    filas = _ejecutar(
        "CREATE TABLE WORK.r AS SELECT * FROM A OUTER UNION CORR SELECT * FROM B "
        "OUTER UNION CORR SELECT * FROM C;",
        {"A": a, "B": b, "C": c},
    )
    assert filas == [(1, "A", None), (2, None, "B"), (3, None, None)]
