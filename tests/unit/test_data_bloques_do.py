"""`IF ... THEN DO; ... END; ELSE ...` baja a una asignación condicional por columna."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _correr(cuerpo: str, filas: list[dict]) -> list[dict]:
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan
    return ejecutar_plan(plan, {"t": filas})["r"]


def test_bloque_con_else_asigna_cada_columna_por_rama():
    filas = [{"s": "-5", "k": "x"}, {"s": "10", "k": "y"}, {"s": "", "k": "z"}]

    salida = _correr(
        "  IF s < 0 THEN DO;\n    marca = 'SI';\n    s = 0;\n  END;\n  ELSE marca = 'NO';\n", filas
    )

    # Un faltante es menor que cualquier número: también entra en la rama THEN.
    assert [(f["marca"], f["s"]) for f in salida] == [("SI", "0"), ("NO", "10"), ("SI", "0")]


def test_la_columna_que_la_condicion_lee_se_asigna_la_ultima():
    salida = _correr(
        "  IF s < 0 THEN DO;\n    s = 0;\n    marca = 'SI';\n  END;\n  ELSE marca = 'NO';\n",
        [{"s": "-5"}],
    )

    # `marca` se evalúa con el `s` original aunque en el SAS `s` se asigne primero.
    assert salida[0]["marca"] == "SI" and salida[0]["s"] == "0"


def test_cadena_con_else_if_y_bloques():
    cuerpo = (
        "  IF n > 10 THEN DO;\n    g = 'alto';\n  END;\n"
        "  ELSE IF n > 5 THEN DO;\n    g = 'medio';\n  END;\n"
        "  ELSE DO;\n    g = 'bajo';\n  END;\n"
    )

    salida = _correr(cuerpo, [{"n": "20"}, {"n": "7"}, {"n": "1"}])

    assert [f["g"] for f in salida] == ["alto", "medio", "bajo"]


def test_una_columna_asignada_dos_veces_en_la_rama_no_se_inventa():
    texto = (
        ENTRADA
        + "DATA WORK.r;\n  SET WORK.t;\n  IF n > 1 THEN DO;\n    a = 1;\n    a = a + 1;\n  END;\nRUN;\n"
    )
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan

    derivaciones = [
        paso
        for op in plan.graph.operators()
        for paso in (op.params.get("steps") or [{"kind": op.kind, "params": op.params}])
        if paso.get("kind") == "derive"
    ]
    # Sigue el camino de siempre (con su nota): ninguna asignación condicional inventada.
    assert not any(
        "conditional" in asignacion
        for paso in derivaciones
        for asignacion in paso["params"].get("assignments", [])
    )
