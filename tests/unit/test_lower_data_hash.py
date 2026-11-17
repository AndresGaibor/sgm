"""B-21: los objetos hash del DATA step no son pasos soportados, y no sale ningún Job con ellos.

Cada método lleva su código de pendiente (`lrcon`: `FIND` p. 634, `ADD` p. 633, reemplazar y quitar
p. 638, `OUTPUT` del hash p. 639, el iterador p. 642). Un hueco hace que el Job no se escriba.
"""

from __future__ import annotations

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _plan(cuerpo: str):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _huecos(plan):
    return [op for op in plan.graph.operators() if op.status == "hueco"]


def test_declare_hash_y_find_son_un_hueco_con_su_codigo_y_su_pagina():
    plan = _plan("  DECLARE HASH h(dataset: 'work.b');\n  rc = h.find();\n")
    huecos = _huecos(plan)
    assert huecos, "un objeto hash debe quedar como hueco"
    assert all(h.params["codigo"] == "P-HASH-LOOKUP-SIN-SOPORTE" for h in huecos)
    assert any("lrcon, p. 634" in n for h in huecos for n in h.notes)


def test_add_es_p_hash_mutable_y_no_sale_derive_del_metodo():
    plan = _plan("  DECLARE HASH h(dataset: 'work.b');\n  rc = h.add();\n  z = y;\n")
    huecos = _huecos(plan)
    assert any(op.params.get("codigo") == "P-HASH-MUTABLE" for op in huecos)
    derivados = [op for op in plan.graph.operators() if op.kind == "derive"]
    assert not any("h.add" in str(op.params.get("assignments")) for op in derivados)


def test_output_del_hash_y_iterador_tienen_su_codigo():
    plan = _plan("  DECLARE HASH h(dataset: 'work.b');\n  h.output(dataset: 'work.salida');\n")
    assert any(op.params.get("codigo") == "P-HASH-OUTPUT" for op in _huecos(plan))
    plan = _plan("  DECLARE HITER it('h');\n  it.first();\n")
    assert any(op.params.get("codigo") == "P-HASH-ITERADOR" for op in _huecos(plan))


def test_programa_con_hash_no_emite_job(tmp_path):
    """Anillo A (B-21 paso c): un `h.add()` deja pendiente y ningún Job parcial."""
    programa = tmp_path / "hash.sas"
    programa.write_text(
        ENTRADA
        + "DATA WORK.r;\n  SET WORK.t;\n  DECLARE HASH h(dataset: 'work.b');\n"
        + "  rc = h.add();\nRUN;\nPROC EXPORT DATA=WORK.r OUTFILE='.../r.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    muestra = tmp_path / "muestra"
    muestra.mkdir()
    (muestra / "T.csv").write_text("ID,Y\n1,2\n", encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    assert resultado.jobs == []
    assert "P-HASH-MUTABLE" in {p.codigo for p in resultado.pendientes}
