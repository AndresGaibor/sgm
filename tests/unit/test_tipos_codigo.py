"""Tipos que el propio código SAS demuestra (R7): informats, put, cast, literales y declaraciones."""

from sgm.compile import compile_project
from sgm.ir.models import Column
from sgm.ir.types_code import CodeType, declared_types, expression_type, informat_type
from sgm.passes.p09_schemas import _with_derived


def _columns(compiled) -> dict[str, Column]:
    """Columnas con tipo de los operadores derive del programa (por nombre)."""
    found: dict[str, Column] = {}
    for op in compiled.plan.graph.operators():
        for column in op.schema or []:
            if column.type is not None:
                found.setdefault(column.name, column)
    return found


def test_informat_numerico_segun_ancho_y_decimales():
    assert informat_type("8.") == CodeType("Long")
    assert informat_type("30.2") == CodeType("BigDecimal")
    assert informat_type("20.") == CodeType("Double")  # ancho mayor que 18 sin decimales
    assert informat_type("dollar18.2") == CodeType("BigDecimal")
    assert informat_type("comma12.") == CodeType("Long")


def test_informat_de_texto_y_de_fecha():
    assert informat_type("$10.") == CodeType("String", 10)
    assert informat_type("char5.") == CodeType("String", 5)
    assert informat_type("yymmdd8.") == CodeType("Date")
    assert informat_type("datetime20.") == CodeType("Date")


def test_input_y_put_de_la_expresion():
    assert expression_type("input(x, 8.)") == CodeType("Long")
    assert expression_type("input(x, 8.2)") == CodeType("BigDecimal")
    assert expression_type("input(x, yymmdd8.)") == CodeType("Date")
    assert expression_type("put(x, 8.)") == CodeType("String", 8)


def test_cast_de_sql_y_literales():
    assert expression_type("CAST(x AS INT)") == CodeType("Integer")
    assert expression_type("CAST(x AS VARCHAR(20))") == CodeType("String", 20)
    assert expression_type("'abc'") == CodeType("String")
    assert expression_type("42") == CodeType("Long")
    assert expression_type("1.5") == CodeType("Double")
    assert expression_type("2 * 3") == CodeType("Double")


def test_una_variable_no_tiene_tipo_que_el_codigo_fije():
    assert expression_type("x + 1") is None
    assert expression_type("int(x) + y") is None  # no es una sola llamada: no fija el tipo


def test_funciones_de_caracter_y_numericas_fijan_el_tipo():
    assert expression_type("COMPRESS(input(left(VAR12), 30.))") == CodeType("String")
    assert expression_type("SUBSTRN(CATS(NOMBRE), 1, 5)") == CodeType("String")
    assert expression_type("int(x / 2)") == CodeType("Double")
    assert expression_type("round(y, 0.01)") == CodeType("Double")


def test_declaraciones_length_format_e_informat():
    found = declared_types(
        [
            ("length", "nro $ 30"),
            ("length", "n 8"),
            ("format", "f dollar18.2"),
            ("informat", "g yymmdd8."),
        ]
    )
    assert found["nro"] == CodeType("String", 30)
    assert found["n"] == CodeType("Long")
    assert found["f"] == CodeType("BigDecimal")
    assert found["g"] == CodeType("Date")


def test_el_catalogo_no_se_pisa_con_el_codigo():
    base = [Column("nro", "String", 10, "catalog")]
    derived = _with_derived(base, [{"target": "nro", "expression": "input(x, 8.)"}], {})
    assert derived[0].type == "String" and derived[0].source == "catalog"


def test_derivada_sin_tipo_del_codigo_sigue_desconocida():
    derived = _with_derived([], [{"target": "z", "expression": "x + y"}], {})
    assert derived[0].type is None and derived[0].source == "derived"


def test_data_step_tipa_las_columnas_que_convierte():
    program = (
        "data work.t;\n"
        "  length nro $ 30;\n"
        "  set work.src;\n"
        "  nro_n = input(VAR1, 8.);\n"
        "  cod = put(VAR2, 10.);\n"
        "  s = 'a';\n"
        "  x = 2 * 3;\n"
        "  z = w + 1;\n"
        "run;\n"
    )
    compiled, _ = compile_project({"p.sas": program})
    columns = _columns(compiled["p.sas"])
    assert columns["nro_n"].type == "Long" and columns["nro_n"].source == "code"
    assert columns["cod"] == Column("cod", "String", 10, "code")
    assert columns["s"].type == "String"
    assert columns["x"].type == "Double"
    assert "z" not in columns  # `w + 1`: el código no fija el tipo de z


def test_cast_de_sql_en_el_programa():
    compiled, _ = compile_project(
        {
            "p.sas": "proc sql;\ncreate table work.t as select cast(a as integer) as ai from work.s;\nquit;\n"
        }
    )
    assert _columns(compiled["p.sas"])["ai"].type == "Integer"
