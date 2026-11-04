"""Extracción de tablas leídas por PROC SQL (`extract_sources` y `parse_sql_statement`).

Todos los casos usan nombres inventados.
"""

import pytest

from sgm.frontend.sql import parse_sql_statement
from sgm.frontend.sql_fuentes import extract_sources

# --- fallos de la auditoría: falsos positivos en funciones ----------------


def test_from_de_extract_no_es_fuente():
    assert extract_sources("select extract(year from x) as y, a from t") == ("t",)


def test_from_de_substring_no_es_fuente():
    assert extract_sources("select substring(a from 2) from t") == ("t",)


def test_from_de_trim_con_both_no_es_fuente():
    assert extract_sources("select trim(both ' ' from z) from t") == ("t",)


def test_funcion_con_from_y_sin_from_real_no_devuelve_nada():
    assert extract_sources("select extract(day from fecha) as d") == ()


# --- fallos de la auditoría: listas con coma y joins ----------------------


def test_lista_con_coma_en_from_devuelve_todas():
    assert extract_sources("select a from b, c, d") == ("b", "c", "d")


def test_lista_con_coma_y_alias_no_pierde_tablas():
    assert extract_sources("select a from b, c d, e as f") == ("b", "c", "e")


def test_inner_join_con_alias_y_con_as():
    assert extract_sources("select a from x inner join y as z on x.k = z.k") == ("x", "y")


def test_left_right_full_join_sin_alias():
    sql = "select a from x left join y on 1=1 right join z on 1=1 full join w on 1=1"
    assert extract_sources(sql) == ("x", "y", "z", "w")


def test_join_con_alias_sin_as():
    assert extract_sources("select a from x xa join y ya on xa.k = ya.k") == ("x", "y")


def test_cross_y_natural_join():
    assert extract_sources("select a from x cross join y natural join z") == ("x", "y", "z")


def test_left_outer_join_con_alias():
    assert extract_sources("select a from x as p left outer join y q on p.k = q.k") == ("x", "y")


def test_coma_despues_de_join_con_on():
    sql = "select a from x join y on x.k = y.k, z"
    assert extract_sources(sql) == ("x", "y", "z")


def test_alias_de_tabla_no_es_fuente():
    assert extract_sources("select t.a from tabla_real t1 where t1.a = 1") == ("tabla_real",)


def test_alias_con_as_no_es_fuente():
    assert extract_sources("select a from tabla_real as t1, otra as t2") == (
        "tabla_real",
        "otra",
    )


def test_nombre_con_libreria_se_conserva_tal_cual():
    assert extract_sources("select a from lib.tabla t join otra.dos d on 1=1") == (
        "lib.tabla",
        "otra.dos",
    )


# --- subconsultas ---------------------------------------------------------


def test_subconsulta_en_from_devuelve_sus_tablas_y_no_su_alias():
    assert extract_sources("select s.a from (select a from interna) as s, externa o") == (
        "interna",
        "externa",
    )


def test_subconsulta_en_from_con_join():
    sql = "select a from x join (select k from y where k > 0) s on x.k = s.k"
    assert extract_sources(sql) == ("x", "y")


def test_subconsulta_en_where_in():
    assert extract_sources("select a from t where k in (select k from u)") == ("t", "u")


def test_subconsulta_en_exists():
    sql = "select a from t where exists (select 1 from v where v.k = t.k)"
    assert extract_sources(sql) == ("t", "v")


def test_subconsulta_escalar_en_select():
    assert extract_sources("select (select max(a) from m) as mx, b from t") == ("m", "t")


def test_subconsulta_dentro_de_funcion_si_se_recorre():
    sql = "select coalesce((select max(a) from m), 0) as c from t"
    assert extract_sources(sql) == ("m", "t")


# --- CTE --------------------------------------------------------------------


def test_cte_no_es_tabla_y_su_base_si():
    sql = "with c as (select a from base) select a from c join d on 1=1"
    assert extract_sources(sql) == ("base", "d")


def test_cte_con_lista_de_columnas_no_es_tabla():
    sql = "with c (k, v) as (select k, v from base) select k from c"
    assert extract_sources(sql) == ("base",)


# --- orden, duplicados, comillas, comentarios, macrovariables -------------


def test_orden_de_aparicion_y_sin_duplicados():
    sql = "select a from t2 where k in (select k from t1) union select a from t2"
    assert extract_sources(sql) == ("t2", "t1")


def test_union_devuelve_tablas_de_ambas_ramas():
    assert extract_sources("select a from t1 union all select a from t2") == ("t1", "t2")


def test_literal_con_from_no_es_fuente():
    assert extract_sources("select 'from fantasma' as s, a from real") == ("real",)


def test_literal_con_comilla_escapada_no_rompe_el_conteo():
    assert extract_sources("select 'it''s from x' as s from real") == ("real",)


def test_comentario_de_bloque_con_from_no_es_fuente():
    assert extract_sources("select a /* from fantasma */ from real") == ("real",)


def test_comentario_de_linea_con_from_no_es_fuente():
    assert extract_sources("select a from real -- from fantasma") == ("real",)


def test_macrovariable_en_from_se_devuelve_sin_resolver():
    assert extract_sources("select a from &tabla. t") == ("&tabla.",)


def test_macrovariable_en_libreria_se_devuelve_tal_cual():
    assert extract_sources("select a from lib.&nombre") == ("lib.&nombre",)


def test_nombre_entre_comillas_dobles_es_fuente():
    assert extract_sources('select a from "tabla con espacios"') == ('"tabla con espacios"',)


def test_pass_through_no_aporta_tablas_de_sas():
    assert extract_sources("select a from connection to db (select * from remoto)") == ()


# --- sentencias completas ---------------------------------------------------


@pytest.mark.parametrize(
    "sentencia, esperado",
    [
        ("create table lz.t as select a from b, c", ("b", "c")),
        ("insert into lz.t select a from b left join c on 1=1", ("b", "c")),
        ("select a from b where k in (select k from c)", ("b", "c")),
    ],
)
def test_sentencias_completas_usan_la_extraccion(sentencia, esperado):
    st = parse_sql_statement(sentencia, 1)
    assert st.sources == esperado


def test_columnas_separadas_por_coma_en_subconsulta_de_join_no_son_tablas():
    sql = "select a.x from t a left join (select num_doc, llave from m) b on a.k = b.llave"
    assert extract_sources(sql) == ("t", "m")


def test_columnas_separadas_por_coma_en_subconsulta_de_from_no_son_tablas():
    assert extract_sources("select * from (select c1, c2 from base) z") == ("base",)


def test_pass_through_expone_las_tablas_del_motor_como_lecturas():
    sentencia = "create table w.t as select * from connection to impala (select a, b from esq.tabla)"
    st = parse_sql_statement(sentencia, 1)
    assert st.kind == "select_passthrough"
    assert st.sources == ("esq.tabla",)
