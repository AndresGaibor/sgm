"""PROC declarados en YAML (F1.4): qué PROC salen de `rules/sas/procs/` y cuáles siguen en código."""

from sgm.ir.proc_rules import SPECS, declared, names_of


def test_means_summary_freq_append_estan_declarados():
    assert {"means", "summary", "freq", "append"} <= set(SPECS)
    assert declared("means")["ops"][0]["kind"] == "aggregate"


def test_sort_sigue_en_codigo():
    assert declared("sort") is None


def test_names_of_normaliza_la_clausula():
    assert names_of("class Region Sucursal;") == ["region", "sucursal"]
    assert names_of(None) == []
