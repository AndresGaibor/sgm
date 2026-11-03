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
        assert isinstance(j["entradas"], list) and isinstance(j["salidas"], list)


def test_sin_repeticion_no_hay_joblet() -> None:
    assert _joblets("data work.a; set work.b; x = 1; run;\n") == []


def test_parametros_de_joblet_tienen_tipo() -> None:
    """Fase 3.8: cada parámetro del joblet declara si es `tabla` o `literal`."""
    for j in _joblets(PROGRAMA):
        assert set(j["tipos"]) == set(j["parametros"])
        assert set(j["tipos"].values()) <= {"tabla", "literal"}


def test_residuos_son_lista_explicita() -> None:
    """Fase 3.6: los residuos de bloques se listan; ninguna forma sin unificar queda oculta."""
    from sgm.compile import compile_project

    compilados, _ = compile_project({"x.sas": PROGRAMA})
    residuos = compilados["x.sas"].plan.residuos_bloques
    assert isinstance(residuos, list)
    assert all(r["motivo"] == "SEMANTICA_DUDOSA" for r in residuos)
