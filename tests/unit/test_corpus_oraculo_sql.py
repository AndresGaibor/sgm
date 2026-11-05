"""Pruebas del traductor de PROC SQL a SQLite y del oráculo de capa A: una prueba por construcción.

Cada construcción se comprueba de dos formas: la forma traducida del texto, y el resultado al ejecutarla
sobre tablas pequeñas. Las no soportadas deben fallar con NoSoportado y no traducirse en silencio.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.csv_tabla import Tabla  # noqa: E402
from corpus_lib.oraculo_sql import ErrorSql, ejecutar_proc_sql  # noqa: E402
from corpus_lib.sas_texto import ErrorSas, sentencias, sentencias_proc_sql  # noqa: E402
from corpus_lib.traduccion_sql import NoSoportado, a_sqlite  # noqa: E402

FILAS = Tabla(
    ["id", "nombre", "monto", "ciudad"],
    [
        (1, "Ana", 100, "Norte"),
        (2, "Bruno", None, "Sur"),
        (3, "carla", 300, "Norte"),
        (4, "Ana", 150, None),
    ],
    ["INTEGER", "TEXT", "INTEGER", "TEXT"],
)


def _correr(sql_sas: str, salidas: list[str]) -> dict[str, Tabla]:
    """Ejecuta un bloque de PROC SQL sobre la tabla FILAS, llamada DATOS."""
    sentencias_sql = sentencias_proc_sql(f"PROC SQL;\n{sql_sas}\nQUIT;")
    return ejecutar_proc_sql(sentencias_sql, {"DATOS": FILAS}, salidas)


def test_work_se_quita_del_nombre_de_tabla():
    sql = a_sqlite("CREATE TABLE WORK.x AS SELECT id FROM WORK.datos")
    assert sql == "CREATE TABLE x AS SELECT id FROM datos"


def test_is_missing_pasa_a_is_null():
    sql = a_sqlite("SELECT id FROM datos WHERE monto IS MISSING")
    assert sql == "SELECT id FROM datos WHERE monto IS NULL"
    resultado = _correr("CREATE TABLE WORK.r AS SELECT id FROM DATOS WHERE monto IS MISSING;", ["r"])
    assert resultado["r"].filas == [(2,)]


def test_is_not_missing_pasa_a_is_not_null():
    sql = a_sqlite("SELECT id FROM datos WHERE ciudad is not missing")
    assert sql == "SELECT id FROM datos WHERE ciudad IS NOT NULL"


def test_distinto_con_caret_y_tilde_pasa_a_menor_mayor():
    assert a_sqlite("SELECT id FROM t WHERE a ^= 1") == "SELECT id FROM t WHERE a <> 1"
    assert a_sqlite("SELECT id FROM t WHERE a ~= 1") == "SELECT id FROM t WHERE a <> 1"


def test_concatenacion_se_pasa_igual():
    sql = a_sqlite("CREATE TABLE WORK.r AS SELECT nombre || '-' || ciudad AS etq FROM WORK.datos")
    assert "nombre || '-' || ciudad AS etq" in sql
    resultado = _correr(
        "CREATE TABLE WORK.r AS SELECT nombre || '-' || ciudad AS etq FROM DATOS;", ["r"]
    )
    assert resultado["r"].filas[0] == ("Ana-Norte",)


def test_alias_de_tabla_sin_as_funciona():
    resultado = _correr("CREATE TABLE WORK.r AS SELECT d.id FROM DATOS d WHERE d.id = 2;", ["r"])
    assert resultado["r"].filas == [(2,)]


def test_left_join_con_on_entre_parentesis():
    otra = Tabla(["id", "pais"], [(1, "Peru"), (3, "Chile")], ["INTEGER", "TEXT"])
    sql = (
        "CREATE TABLE WORK.r AS SELECT d.id, o.pais FROM DATOS d "
        "LEFT JOIN OTRA o ON (d.id = o.id);"
    )
    resultado = ejecutar_proc_sql(
        sentencias_proc_sql(f"PROC SQL;\n{sql}\nQUIT;"),
        {"DATOS": FILAS, "OTRA": otra},
        ["r"],
    )
    assert resultado["r"].filas == [(1, "Peru"), (2, None), (3, "Chile"), (4, None)]


def test_case_when_se_pasa_igual():
    resultado = _correr(
        "CREATE TABLE WORK.r AS SELECT id, CASE WHEN monto > 120 THEN 'alto' ELSE 'bajo' END AS "
        "nivel FROM DATOS;",
        ["r"],
    )
    # Con monto faltante, la condición es NULL y cae en ELSE.
    assert [fila[1] for fila in resultado["r"].filas] == ["bajo", "bajo", "alto", "alto"]


def test_distinct_se_pasa_igual():
    resultado = _correr("CREATE TABLE WORK.r AS SELECT DISTINCT nombre FROM DATOS;", ["r"])
    assert sorted(fila[0] for fila in resultado["r"].filas) == ["Ana", "Bruno", "carla"]


def test_group_by_y_having_se_pasan_igual():
    resultado = _correr(
        "CREATE TABLE WORK.r AS SELECT nombre, COUNT(*) AS n FROM DATOS GROUP BY nombre "
        "HAVING COUNT(*) > 1;",
        ["r"],
    )
    assert resultado["r"].filas == [("Ana", 2)]


@pytest.mark.parametrize(
    ("funcion", "esperado"),
    [
        ("COUNT(monto)", 3),  # el faltante no cuenta
        ("SUM(monto)", 550),
        ("MIN(monto)", 100),
        ("MAX(monto)", 300),
    ],
)
def test_agregados_ignoran_faltantes(funcion, esperado):
    resultado = _correr(f"CREATE TABLE WORK.r AS SELECT {funcion} AS valor FROM DATOS;", ["r"])
    assert resultado["r"].filas == [(esperado,)]


def test_upcase_y_lowcase_pasan_a_upper_y_lower():
    assert a_sqlite("SELECT UPCASE(nombre) AS a FROM t") == "SELECT upper(nombre) AS a FROM t"
    assert a_sqlite("SELECT lowcase(nombre) AS a FROM t") == "SELECT lower(nombre) AS a FROM t"
    resultado = _correr("CREATE TABLE WORK.r AS SELECT UPCASE(nombre) AS m FROM DATOS;", ["r"])
    assert resultado["r"].filas[0] == ("ANA",)


def test_trim_pasa_a_rtrim_que_quita_solo_blancos_finales():
    assert a_sqlite("SELECT TRIM(nombre) AS a FROM t") == "SELECT rtrim(nombre) AS a FROM t"


def test_like_distingue_mayusculas():
    # "carla" empieza con minúscula: con LIKE sensible a mayúsculas no entra en 'C%'.
    resultado = _correr("CREATE TABLE WORK.r AS SELECT id FROM DATOS WHERE nombre LIKE 'C%';", ["r"])
    assert resultado["r"].filas == []


def test_like_con_guion_bajo_y_porcentaje():
    resultado = _correr("CREATE TABLE WORK.r AS SELECT id FROM DATOS WHERE nombre LIKE 'An_';", ["r"])
    assert [fila[0] for fila in resultado["r"].filas] == [1, 4]


def test_in_lista_se_pasa_igual():
    resultado = _correr("CREATE TABLE WORK.r AS SELECT id FROM DATOS WHERE id IN (2, 4);", ["r"])
    assert resultado["r"].filas == [(2,), (4,)]


def test_between_se_pasa_igual():
    resultado = _correr(
        "CREATE TABLE WORK.r AS SELECT id FROM DATOS WHERE monto BETWEEN 100 AND 150;", ["r"]
    )
    assert [fila[0] for fila in resultado["r"].filas] == [1, 4]


def test_comillas_dobles_pasan_a_comillas_simples():
    assert a_sqlite('SELECT id FROM t WHERE ciudad = "Norte"') == (
        "SELECT id FROM t WHERE ciudad = 'Norte'"
    )
    assert a_sqlite('SELECT id FROM t WHERE x = "it\'s"') == (
        "SELECT id FROM t WHERE x = 'it''s'"
    )


def test_comentarios_se_quitan_y_no_cortan_sentencias():
    sql = a_sqlite("SELECT id /* columna; de prueba */ FROM datos")
    assert sql == "SELECT id   FROM datos"
    partes = sentencias("CREATE TABLE WORK.a AS SELECT 'x;y' AS t FROM d; QUIT;")
    assert partes == ["CREATE TABLE WORK.a AS SELECT 'x;y' AS t FROM d", "QUIT"]


def test_proc_sql_sin_quit_es_error():
    with pytest.raises(ErrorSas):
        sentencias_proc_sql("PROC SQL; CREATE TABLE WORK.a AS SELECT 1 AS x FROM t;")


@pytest.mark.parametrize(
    ("sql", "fragmento"),
    [
        ("SELECT calculated x FROM t", "CALCULATED"),
        ("SELECT id FROM t WHERE x = 1 format = 8.", "FORMAT"),
        ("SELECT id INTO :m FROM t", "INTO"),
        ("SELECT monto / 2 AS m FROM t", "división"),
        ("SELECT monto ** 2 AS m FROM t", "potencia"),
        ("SELECT monto % 2 AS m FROM t", "%"),
        ("SELECT &var AS m FROM t", "macrovariable"),
        ("SELECT CAST(monto AS TEXT) AS m FROM t", "CAST()"),
        ("SELECT id FROM t WHERE f = '01JAN2026'd", "fecha"),
        ('SELECT id FROM t WHERE x = "nombre"n', "sufijo"),
    ],
)
def test_construccion_no_soportada_falla_con_nombre(sql, fragmento):
    with pytest.raises(NoSoportado) as info:
        a_sqlite(sql)
    assert fragmento.lower() in info.value.construccion.lower()


def test_sentencia_fuera_de_create_table_no_soportada():
    with pytest.raises(NoSoportado):
        _correr("SELECT id FROM DATOS;", ["x"])


def test_salida_que_no_se_creo_es_error_claro():
    with pytest.raises(ErrorSql, match="no se creó"):
        _correr("CREATE TABLE WORK.r AS SELECT id FROM DATOS;", ["otra"])


def test_not_in_con_subconsulta_se_pasa_igual():
    # La subconsulta devuelve los ids 3 y 4 (monto 300 y 150); NOT IN deja 1 y 2.
    resultado = _correr(
        "CREATE TABLE WORK.r AS SELECT id FROM DATOS "
        "WHERE id NOT IN (SELECT id FROM DATOS WHERE monto >= 150);",
        ["r"],
    )
    assert [fila[0] for fila in resultado["r"].filas] == [1, 2]


def test_count_distinct_se_pasa_igual():
    resultado = _correr("CREATE TABLE WORK.r AS SELECT COUNT(DISTINCT nombre) AS n FROM DATOS;", ["r"])
    assert resultado["r"].filas == [(3,)]


def test_subconsulta_escalar_en_select_se_pasa_igual():
    resultado = _correr(
        "CREATE TABLE WORK.r AS SELECT (SELECT COUNT(*) FROM DATOS) AS total, COUNT(*) AS filas "
        "FROM DATOS;",
        ["r"],
    )
    assert resultado["r"].filas == [(4, 4)]


def test_alias_asterisco_y_coalesce_con_faltante():
    otra = Tabla(["id", "pais"], [(1, "Peru"), (3, "Chile")], ["INTEGER", "TEXT"])
    sql = (
        "CREATE TABLE WORK.r AS SELECT d.*, COALESCE(d.monto, 0) AS m FROM DATOS d "
        "INNER JOIN OTRA o ON ( d.id = o.id );"
    )
    resultado = ejecutar_proc_sql(
        sentencias_proc_sql(f"PROC SQL;\n{sql}\nQUIT;"),
        {"DATOS": FILAS, "OTRA": otra},
        ["r"],
    )
    assert resultado["r"].columnas == ["id", "nombre", "monto", "ciudad", "m"]
    assert resultado["r"].filas == [(1, "Ana", 100, "Norte", 100), (3, "carla", 300, "Norte", 300)]


def test_orden_descendente_pone_el_faltante_al_final():
    # En SAS el faltante es menor que cualquier número: en DESC queda el último, como en SQLite.
    resultado = _correr("CREATE TABLE WORK.r AS SELECT id FROM DATOS ORDER BY monto DESC;", ["r"])
    assert [fila[0] for fila in resultado["r"].filas] == [3, 4, 1, 2]
