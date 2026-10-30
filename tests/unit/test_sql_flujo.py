"""PROC SQL nunca termina en tJava (R4): cada construcción tiene su operador de flujo.

Las pruebas miran el componente candidato de cada operador, no solo el tipo de operador: el
criterio es que ninguna consulta sobre WORK acabe en `tJava`.
"""

from sgm.compile import compile_project
from sgm.frontend.sql_normalize import normalize
from sgm.ir.sql_tree import SqlParseError, build


def _components(program: str) -> list[tuple[str, str]]:
    """(tipo de operador, componente) de cada operador de flujo del programa."""
    compiled, _ = compile_project({"p.sas": program})
    plan = compiled["p.sas"].plan
    return [
        (op.kind, op.component["name"])
        for op in plan.graph.operators()
        if op.component and op.component["name"] != "none"
    ]


def _kinds(program: str) -> list[str]:
    return [kind for kind, _ in _components(program)]


def _sql(body: str) -> str:
    return f"proc sql;\n{body}\nquit;\n"


def test_where_se_convierte_en_filtro():
    kinds = _kinds(_sql("create table t as select a from s where a > 1;"))
    assert "filter" in kinds


def test_join_on_se_convierte_en_union_por_clave():
    kinds = _kinds(_sql("create table t as select a.k, b.v from s a join r b on a.k = b.k;"))
    assert "join" in kinds


def test_group_by_y_agregados_van_a_tAggregateRow():
    components = _components(_sql("create table t as select k, sum(v) as tot from s group by k;"))
    assert ("aggregate", "tAggregateRow") in components


def test_having_se_aplica_despues_del_agregado_y_usa_el_alias():
    compiled, _ = compile_project(
        {
            "p.sas": _sql(
                "create table t as select k, sum(v) as tot from s group by k having sum(v) > 2;"
            )
        }
    )
    plan = compiled["p.sas"].plan
    texts = [str(op.params) for op in plan.graph.operators()]
    assert any("tot > 2" in text for text in texts)
    assert not plan.gaps


def test_select_con_expresiones_y_alias_va_a_derive():
    kinds = _kinds(_sql("create table t as select a * 2 as doble, b from s;"))
    assert "derive" in kinds or "map" in kinds


def test_distinct_va_a_dedup():
    kinds = _kinds(_sql("create table t as select distinct k from s;"))
    assert "dedup" in kinds


def test_order_by_va_a_sort():
    kinds = _kinds(_sql("create table t as select k from s order by k desc;"))
    assert "sort" in kinds


def test_union_une_las_ramas():
    kinds = _kinds(_sql("create table t as select k from s union all select k from r;"))
    assert "union" in kinds


def test_case_when_queda_como_expresion_pendiente_y_no_es_tjava():
    """El traductor de expresiones no tiene CASE: la expresión queda pendiente, el componente no."""
    program = _sql("create table t as select case when x = 1 then 'a' else 'b' end as c from s;")
    compiled, _ = compile_project({"p.sas": program})
    # El tipo de la columna `c` no lo fija el código: queda como TIPO_DESCONOCIDO (R7).
    assert {g.reason for g in compiled["p.sas"].plan.gaps} <= {
        "FUNCION_NO_MAPEADA",
        "TIPO_DESCONOCIDO",
    }
    assert not any(name == "tJava" for _, name in _components(program))


def test_select_into_va_a_set_variable_no_a_tJava():
    components = _components(_sql("select count(*) into :n from s;"))
    assert ("set_variable", "tSetGlobalVar") in components


def test_calculated_eq_y_comparadores_de_texto_se_normalizan():
    normalized = normalize("select a from s where calculated z eq 1 and w ne 2 and v ge 3")
    assert "calculated" not in normalized.text.lower()
    assert "=" in normalized.text and "<>" in normalized.text and ">=" in normalized.text
    build(normalized.text)  # debe poder parsearse


def test_contains_se_convierte_en_like():
    normalized = normalize("select a from s where nombre contains 'ana'")
    assert "LIKE" in normalized.text.upper()


def test_is_missing_se_convierte_en_comprobacion_de_nulo():
    compiled, _ = compile_project(
        {"p.sas": _sql("create table t as select a from s where a is missing;")}
    )
    filters = [op for op in compiled["p.sas"].plan.graph.operators() if op.kind == "filter"]
    assert filters and "missing(a)" in filters[0].params["expression"]


def test_into_con_separador_guarda_la_variable_y_el_separador():
    normalized = normalize('select name into :lista separated by "|" from dictionary.columns')
    assert normalized.into_vars == [("lista", '"|"')]
    assert "into" not in normalized.text.lower()


def test_macro_variable_en_el_nombre_de_la_tabla_se_recupera():
    normalized = normalize("create table work.&tbl as select a from s")
    assert normalized.restore("mv_tbl") == "&tbl"


def test_opcion_de_dataset_se_quita_con_nota():
    normalized = normalize("select a from lz.tabla (where=(a > 1))")
    assert "where" not in normalized.text.lower()
    assert any("where" in note for note in normalized.notes)


def test_funcion_sin_equivalente_queda_pendiente_sin_cambiar_el_componente():
    components = _components(_sql("create table t as select a from s where mifuncion(a) > 1;"))
    assert ("filter", "tFilterRow") in components or ("filter", "tMap") in components
    assert not any(name == "tJava" for _, name in components)


def test_sql_que_no_parsea_es_parse_error():
    compiled, _ = compile_project({"p.sas": _sql("create table t as select from from where ;")})
    reasons = [g.reason for g in compiled["p.sas"].plan.gaps]
    assert "PARSE_ERROR" in reasons
    assert not any(
        name == "tJava"
        for _, name in _components(_sql("create table t as select from from where ;"))
    )


def test_parse_error_directo_del_arbol():
    try:
        build("create table t as select from from where ;")
    except SqlParseError:
        return
    raise AssertionError("debería fallar")


def test_ningun_proc_sql_sobre_work_termina_en_tjava_en_el_ejemplo_del_cliente():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    text = (root / "tests/fixtures/sas/client/client_poc.sas").read_text(
        encoding="utf-8", errors="replace"
    )
    compiled, _ = compile_project({"client_poc.sas": text})
    plan = compiled["client_poc.sas"].plan
    sql_java = [
        op
        for op in plan.graph.operators()
        if op.component
        and op.component["name"] == "tJava"
        and op.origin is not None
        and op.origin.startswith("proc_sql")
    ]
    assert sql_java == []
