"""Decisiones pendientes agrupadas por firma (R9)."""

from sgm import decisions
from sgm.batch import compile_batch

PROGRAMA = "data a; set s; where x > 1; run;\n"


def test_una_firma_compartida_por_dos_archivos_se_cuenta_una_vez_por_firma():
    compiled, _ = compile_batch({"a.sas": PROGRAMA, "b.sas": PROGRAMA}, workers=1)
    groups = decisions.group(compiled)
    assert groups, "el filtro tiene alternativas: debe haber decisión pendiente"
    shared = groups[0]
    assert shared.operators == 2  # un operador por archivo
    assert shared.files == {"a.sas", "b.sas"}


def test_los_totales_distinguen_decisiones_de_firmas_unicas():
    compiled, _ = compile_batch({"a.sas": PROGRAMA, "b.sas": PROGRAMA}, workers=1)
    totals = decisions.totals(compiled)
    assert totals["decisiones"] == 2
    assert totals["firmas"] == 1


def test_un_programa_sin_alternativas_no_tiene_decisiones():
    compiled, _ = compile_batch({"a.sas": "data a; set s; run;\n"}, workers=1)
    assert decisions.group(compiled) == []
    assert decisions.totals(compiled) == {"decisiones": 0, "firmas": 0}
