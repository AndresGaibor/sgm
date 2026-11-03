"""Fase 4.2 de `docs/automatizacion/03-plan-produccion.md`: mapa de flujo desde hechos."""

from __future__ import annotations

from sgm.facts.mapa import mapa_markdown
from sgm.facts.project import facts_for_project

PROGRAMA = (
    "%let ambiente = D;\n"
    "proc sql;\n"
    "connect to impala (dsn=IMPALA user=ana password='secreto-123');\n"
    "quit;\n"
    "data work.resumen;\n"
    "set work.base;\n"
    "run;\n"
)


def _mapa() -> str:
    hechos = facts_for_project({"prog.sas": PROGRAMA})["prog.sas"]
    return mapa_markdown("prog.sas", hechos)


def test_mapa_tiene_las_secciones_del_diseno() -> None:
    texto = _mapa()
    for seccion in (
        "## Resumen",
        "## Conjuntos de datos",
        "## Entradas y salidas externas",
        "## Conexiones a base",
        "## Ramas por valor de ambiente",
        "## Pendientes",
    ):
        assert seccion in texto


def test_conjuntos_de_datos_muestran_escritura_y_lectura() -> None:
    texto = _mapa()
    assert "| work.resumen | work | 5 | 0 | 0 |" in texto
    assert "| work.base | work | - | 1 | 0 |" in texto


def test_el_mapa_no_muestra_secretos() -> None:
    assert "secreto-123" not in _mapa()


def test_dos_cadenas_independientes_son_dos_etapas() -> None:
    """Fase 4.2: pasos sin datos en común forman etapas distintas."""
    texto = (
        "/* Etiqueta: Cadena A */\n"
        "data work.a1; set work.s1; run;\n"
        "data work.a2; set work.a1; run;\n"
        "/* Etiqueta: Cadena B */\n"
        "data work.b1; set work.t1; run;\n"
    )
    hechos = facts_for_project({"p.sas": texto})["p.sas"]
    filas = [l for l in mapa_markdown("p.sas", hechos).split("\n") if l.startswith("| ") and "Etapa" not in l]
    etapas = [ln for ln in filas if ln.split("|")[1].strip().isdigit()]
    assert len(etapas) == 2
