"""Fase 3.7 de `docs/automatizacion/03-plan-produccion.md`: joblets por forma repetida.

Un bloque de la misma forma que aparece varias veces es un joblet: una unidad por forma, con
sus apariciones (sumadas aunque estén en nodos distintos) y sus parámetros.
"""

from __future__ import annotations

from sgm.compile import compile_project

PROGRAMA = """/* Etiqueta: Bloque A */
data work.a1; set work.s1; x = 1; y = x + 2; z = y * 3; run;
data work.a2; set work.s2; x = 1; y = x + 2; z = y * 3; run;
data work.a3; set work.s3; x = 1; y = x + 2; z = y * 3; run;
/* Etiqueta: Bloque B */
data work.b1; set work.t1; x = 1; y = x + 2; z = y * 3; run;
data work.b2; set work.t2; x = 1; y = x + 2; z = y * 3; run;
"""


def _joblets(texto: str) -> list[dict]:
    compilados, _ = compile_project({"x.sas": texto})
    return compilados["x.sas"].plan.joblets


def test_bloque_repetido_en_dos_nodos_es_un_solo_joblet() -> None:
    joblets = _joblets(PROGRAMA)
    assert len(joblets) == 1
    j = joblets[0]
    assert j["apariciones"] == 5
    assert sorted(j["etiquetas"]) == ["Bloque A", "Bloque B"]


def test_invariantes_de_joblet() -> None:
    for j in _joblets(PROGRAMA):
        assert j["apariciones"] >= 2
        assert len(j["operaciones"]) >= 3
        claves = {k for inst in j["instancias"] for k in inst}
        assert claves == set(j["parametros"])
        assert len(j["fuente"]) == j["apariciones"]


def test_sin_repeticion_no_hay_joblet() -> None:
    assert _joblets("data work.a; set work.b; x = 1; run;\n") == []
