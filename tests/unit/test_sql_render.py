"""SQL de base (dialecto Hive) generado desde el árbol de un PROC SQL, y normalización de SAS."""

import pytest
import sqlglot

from sgm.frontend.sql_normalize import normalize
from sgm.ir.sql_render import render
from sgm.ir.sql_tree import build


def _render(sql: str) -> str:
    normalized = normalize(sql)
    return render(build(normalized.text), normalized)


def test_render_une_join_filtro_y_agrupado_en_hive():
    text = _render(
        "create table t as select a.k, sum(b.n) as total from s a left join r b "
        "on a.k = b.k where a.v > 1 group by a.k"
    )
    assert "LEFT JOIN" in text and "GROUP BY" in text and "WHERE" in text
    sqlglot.parse_one(text, read="hive")  # el resultado es SQL de Hive válido


def test_render_conserva_union_all_y_orden():
    text = _render("select k from s union all select k from r order by k desc")
    assert "UNION ALL" in text
    sqlglot.parse_one(text, read="hive")


def test_render_no_escribe_sql_con_macro_variable_en_el_destino():
    """Un destino `work.&tbl` no tiene SQL de base fijo: el render lo rechaza (ValueError)."""
    normalized = normalize("create table work.&tbl as select a from s")
    assert normalized.restore("work.mv_tbl") == "work.&tbl"
    with pytest.raises(ValueError):
        render(build(normalized.text), normalized)


def test_fecha_de_sas_se_queda_como_texto():
    normalized = normalize('select a from s where f between "01jan2024"d and "31jan2024"d')
    assert "d AND" not in normalized.text and "'01jan2024'" in normalized.text


def test_format_del_select_se_quita():
    normalized = normalize("select sum(v) as total format=dollar18.2 from s")
    assert "format" not in normalized.text.lower()
    build(normalized.text)
