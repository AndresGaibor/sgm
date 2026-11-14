"""Guardas de estructura para conservar una sola implementación de cada función SAS."""

import ast
from collections import defaultdict
from pathlib import Path

from sgm.expressions import talend_tabla

EXPRESSIONS = Path(__file__).resolve().parents[2] / "src" / "sgm" / "expressions"
# Constructores SAS de D1-6; las utilidades del lexer/base/core quedan fuera del alcance.
SAS_BUILDERS = {
    "_aggregate", "_cat", "_coalesce", "_compress", "_datepart", "_ifv", "_input",
    "_int", "_intck", "_intnx", "_mdy", "_part", "_put", "_round", "_scan",
    "_strfn", "_substr", "_unary_math",
}
# Capturada antes de la refactorización: no se calcula con la tabla bajo prueba.
FUNCTION_NAMES = (
    "abs", "cat", "cats", "catt", "catx", "ceil", "coalesce", "coalescec", "compbl",
    "compress", "count", "date", "datepart", "datetime", "day", "exp", "floor", "ifc",
    "ifn", "index", "input", "inputc", "inputn", "int", "intck", "intnx", "left",
    "length", "lengthc", "lengthn", "log", "lowcase", "max", "mdy", "mean", "min",
    "missing", "mod", "month", "n", "nmiss", "propcase", "put", "putc", "putn", "repeat",
    "reverse", "right", "round", "scan", "sqrt", "strip", "substr", "substrn", "sum",
    "today", "tranwrd", "trim", "upcase", "weekday", "year",
)


def test_sas_builders_have_one_module_level_definition():
    """Una copia nueva de SCAN u otro constructor SAS debe fallar aunque no se importe."""
    definitions = defaultdict(list)
    for path in sorted(EXPRESSIONS.glob("talend_*.py")):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in SAS_BUILDERS:
                    definitions[node.name].append(path.name)
    invalid = {name: definitions[name] for name in sorted(SAS_BUILDERS) if len(definitions[name]) != 1}
    assert not invalid, f"Constructores SAS sin definición única: {invalid}"


def test_talend_modules_have_at_most_300_lines():
    oversized = {
        path.name: count
        for path in sorted(EXPRESSIONS.glob("talend_*.py"))
        if (count := len(path.read_text(encoding="utf-8").splitlines())) > 300
    }
    assert not oversized, f"Módulos Talend con más de 300 líneas: {oversized}"


def test_supported_function_names_are_preserved():
    assert sorted(talend_tabla._FUNCTIONS) == list(FUNCTION_NAMES)
