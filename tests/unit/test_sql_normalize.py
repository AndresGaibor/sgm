"""Normalizador de SQL SAS: construcciones de SAS que no son SQL estándar.

Todos los casos usan datos inventados; ninguna sentencia reproduce texto del cliente.
"""

from sgm.compile import compile_project
from sgm.frontend.sql_normalize import normalize
from sgm.ir.sql_tree import build


def _kinds(program: str) -> list[str]:
    compiled, _ = compile_project({"p.sas": program})
    plan = compiled["p.sas"].plan
    return [op.kind for op in plan.graph.operators()]


def _gaps(program: str) -> list[str]:
    compiled, _ = compile_project({"p.sas": program})
    plan = compiled["p.sas"].plan
    return [op.params.get("reason") for op in plan.graph.operators() if op.params.get("reason")]


_SQL = "proc sql;\n{}\nquit;\n"


def _parse(body: str):
    return build(normalize(body).text)


def test_name_literal_se_convierte_a_identificador():
    norm = normalize("select t.'Un Nombre Con Espacios'n from t")
    assert '"Un Nombre Con Espacios"' in norm.text
    assert "name literals" in " ".join(norm.notes)


def test_name_literal_con_apostrofe_escapada():
    norm = normalize("select t.'O''Brien'n from t")
    assert "\"O'Brien\"" in norm.text


def test_label_simple_se_quita_y_se_anota():
    norm = normalize("select ('texto') label='etiqueta' as c from t")
    assert "label" not in norm.text.lower()
    assert "LABEL" in " ".join(norm.notes)


def test_label_con_comillas_dobles_se_quita():
    norm = normalize('select (\'texto\') LABEL="etiqueta" as c from t')
    assert "LABEL" not in norm.text.upper()


def test_informat_de_input_se_pasa_a_cadena():
    norm = normalize("select input(x, w1.) from t")
    assert "input(x, 'w1.')" in norm.text
    norm = normalize("select input(x, datetime20.) from t")
    assert "input(x, 'datetime20.')" in norm.text


def test_informat_numerico_puro_no_se_toca():
    norm = normalize("select input(x, 30.) from t")
    assert "30." in norm.text


def test_formato_desnudo_en_input_se_pasa_a_cadena():
    # Regla existente del normalizador: un argumento `30.` desnudo se pasa a cadena.
    norm = normalize("select input(x, 30.) from t")
    assert "input(x, '30.')" in norm.text


def test_missing_de_comparacion_a_is_null():
    norm = normalize("select x from t where x = .")
    assert "IS NULL" in norm.text
    norm = normalize("select x from t where x <> .")
    assert "IS NOT NULL" in norm.text


def test_missing_con_numero_decimal_no_se_toca():
    norm = normalize("select x from t where x = .5")
    assert "IS NULL" not in norm.text


def test_not_igual_de_sas_a_distinto():
    norm = normalize("select x from t where x not = 3")
    assert "<> 3" in norm.text


def test_circunflejo_igual_de_sas_a_distinto():
    norm = normalize("select x from t where x ^= 3")
    assert "<> 3" in norm.text


def test_contains_literal_se_reescribe():
    norm = normalize("select x from t where x contains 'abc'")
    assert "LIKE CONCAT('%', 'abc', '%')" in norm.text


def test_contains_sin_espacio_antes_del_literal():
    norm = normalize("select x from t where x contains'abc'")
    assert "LIKE CONCAT('%', 'abc', '%')" in norm.text


def test_contains_con_llamada_anidada_a_la_derecha():
    norm = normalize("select x from t where upper(x) contains upper('abc')")
    assert "upper(x) LIKE CONCAT('%', upper('abc'), '%')" in norm.text


def test_contains_con_llamada_anidada_a_la_izquierda():
    norm = normalize("select x from t where upper(trim(x)) contains 'abc'")
    assert "upper(trim(x)) LIKE CONCAT('%', 'abc', '%')" in norm.text


def test_not_contains_se_reescribe():
    norm = normalize("select x from t where x not contains 'abc'")
    assert "NOT LIKE CONCAT('%', 'abc', '%')" in norm.text


def test_not_contains_con_llamada():
    norm = normalize("select x from t where upper(x) not contains upper('abc')")
    assert "upper(x) NOT LIKE CONCAT('%', upper('abc'), '%')" in norm.text


def test_contains_dentro_de_comillas_no_se_toca():
    norm = normalize("select 'a contains b' from t")
    assert "LIKE" not in norm.text


def test_parseo_de_sentencia_con_construcciones_sas():
    tree = _parse(
        "create table out as select t.'Un Campo Raro'n, input(x, w1.) as n from t where x ^= .;"
    )
    assert tree.target and tree.target.upper() == "OUT"


def test_normalizador_protege_solo_funciones_multiargumento_fuera_de_literales():
    normalized = normalize(
        "select sum(a, max(b, c)) as total, 'sum(x, y)' as literal from t /* max(x, y) */"
    )

    assert "sgm_row_sum(a, sgm_row_max(b, c))" in normalized.text.lower()
    assert "'sum(x, y)'" in normalized.text.lower()
    assert "/* max(x, y) */" in normalized.text.lower()


def test_normalizador_protege_funcion_separada_del_parentesis_por_comentario():
    normalized = normalize("select sum /* nota */ (a, b) as total from t")

    assert "sgm_row_sum /* nota */ (a, b)" in normalized.text.lower()
    _parse(normalized.text)


def test_normalizador_no_extiende_un_literal_desde_apostrofe_en_comentario():
    normalized = normalize("select /* client's note */ sum(a, b), 'literal' from t")

    assert "sgm_row_sum(a, b)" in normalized.text.lower()
    assert "/* client's note */" in normalized.text.lower()


def test_normalizador_aplica_operadores_despues_de_comentario_con_apostrofe():
    normalized = normalize("select /* client's note */ a eq 1, sum(b, c), 'literal' from t")

    assert "/* client's note */" in normalized.text.lower()
    assert "a = 1" in normalized.text.lower()
    assert "sgm_row_sum(b, c)" in normalized.text.lower()


def test_normalizador_reescribe_contains_despues_de_comentario_con_apostrofe():
    normalized = normalize("select /* client's note */ x contains 'abc' from t")

    assert "/* client's note */" in normalized.text.lower()
    assert "x like concat('%', 'abc', '%')" in normalized.text.lower()


def _sql(body: str) -> str:
    return _SQL.format(body)


def test_outer_union_corr_es_semantica_dudosa_no_parse_error():
    program = _sql("create table t as select a from s outer union corr select a from r;")
    assert "unsupported" in _kinds(program)
    assert "SEMANTICA_DUDOSA" in _gaps(program)
    assert "PARSE_ERROR" not in _gaps(program)


def test_outer_union_es_semantica_dudosa_no_parse_error():
    program = _sql("create table t as select a from s outer union select a from r;")
    assert "SEMANTICA_DUDOSA" in _gaps(program)
