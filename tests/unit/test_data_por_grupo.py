"""`BY` con `FIRST.`, `LAST.`, `RETAIN` y suma: un programa por fila con estado."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _correr(cuerpo: str, filas: list[dict]):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan
    return plan, ejecutar_plan(plan, {"t": filas})["r"]


FILAS = [
    {"d": "a", "m": "10"},
    {"d": "a", "m": ""},  # faltante: la suma lo ignora
    {"d": "a", "m": "5"},
    {"d": "b", "m": "7"},
]


def test_el_acumulado_se_reinicia_en_cada_grupo_y_ignora_el_faltante():
    plan, salida = _correr("  BY d;\n  IF FIRST.d THEN acum = 0;\n  acum + m;\n", FILAS)

    assert [f["acum"] for f in salida] == [10, 10, 15, 7]
    assert any(op.kind == "stateful_row" for op in plan.graph.operators())


def test_last_deja_una_fila_por_grupo_y_conserva_la_ultima():
    _, salida = _correr("  BY d;\n  IF LAST.d;\n", FILAS)

    assert [(f["d"], f["m"]) for f in salida] == [("a", "5"), ("b", "7")]


def test_retain_con_valor_inicial_cuenta_filas_por_grupo():
    _, salida = _correr(
        "  BY d;\n  RETAIN n 0;\n  IF FIRST.d THEN n = 0;\n  n + 1;\n", FILAS
    )

    assert [f["n"] for f in salida] == [1, 2, 3, 1]


def test_con_dos_llaves_first_de_la_segunda_vale_uno_cuando_cambia_la_primera():
    filas = [{"a": "1", "b": "x"}, {"a": "1", "b": "x"}, {"a": "2", "b": "x"}]

    _, salida = _correr("  BY a b;\n  IF FIRST.b THEN n = 0;\n  n + 1;\n", filas)

    # La tercera fila repite `b` pero cambió `a`: para el SAS es el primer `b` de su grupo.
    assert [f["n"] for f in salida] == [1, 2, 1]
