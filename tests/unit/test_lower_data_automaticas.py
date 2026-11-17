"""B-20: `_N_` y `_ERROR_` no se traducen como columnas: la sentencia sale `hueco` con su motivo."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _plan(cuerpo: str):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _huecos(plan) -> list:
    return [op for op in plan.graph.operators() if op.status == "hueco"]


def test_n_en_una_asignacion_no_se_traduce_como_columna():
    plan = _plan("  n = _n_;\n")
    huecos = _huecos(plan)
    assert len(huecos) == 1
    assert "P-VARIABLE-AUTOMATICA" in huecos[0].notes[0]
    assert not any("_n_" in str(op.params.get("assignments", "")) for op in plan.graph.operators())


def test_error_en_una_condicion_da_el_codigo_de_error():
    plan = _plan("  IF _error_ THEN e = 1;\n")
    assert any("P-ERROR-AUTOMATICA" in op.notes[0] for op in _huecos(plan))


def test_el_texto_entre_comillas_no_cuenta():
    plan = _plan("  x = '_n_';\n")
    assert _huecos(plan) == []


def test_un_nombre_que_solo_contiene_n_no_cuenta():
    plan = _plan("  nombre_n = 1;\n")
    assert _huecos(plan) == []
