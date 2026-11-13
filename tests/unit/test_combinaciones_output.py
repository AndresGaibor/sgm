"""B-17: el generador de combinaciones de `OUTPUT` y su oráculo independiente.

El oráculo (`tools/corpus_output/oraculo.py`) no importa el traductor. Estas pruebas comprueban que su
resultado coincide con el intérprete del plan para cada combinación del espacio, y que una alteración a
mano del esperado sí se detecta (prueba de mutación, MG-P10-06).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import tempfile  # noqa: E402

from corpus_output.gramatica import DATASETS, Combinacion, combinaciones, negativos  # noqa: E402
from corpus_output.oraculo import esperado  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.desplegar import plan_desplegado  # noqa: E402
from sgm.migrar.esquemas import esquemas_de_entrada  # noqa: E402
from sgm.migrar.interprete import ejecutar_plan  # noqa: E402
from sgm.talend_item.desde_plan import plan_a_jobs  # noqa: E402
from sgm.talend_item.validador import validar_job  # noqa: E402

# Valores que ejercen cada rama (< 2, entre 2 y 4, >= 4) y un faltante.
ENTRADAS = [
    {"ID": "a", "VALOR": "-1"},
    {"ID": "b", "VALOR": "0"},
    {"ID": "c", "VALOR": "3"},
    {"ID": "d", "VALOR": "5"},
    {"ID": "e", "VALOR": ""},
]


def _normal(filas: list[dict]) -> list[tuple]:
    """Filas como (ID, VALOR): el intérprete usa nombres en minúscula y el oráculo en mayúscula."""

    def numero(v):
        return None if v in (None, "") else float(v)

    minusculas = [{k.lower(): v for k, v in f.items()} for f in filas]
    return [((f.get("id") or None), numero(f.get("valor"))) for f in minusculas]


def _interprete(programa: str) -> dict[str, list[dict]]:
    plan = compile_file(
        analyze_program({"p.sas": programa}), "p.sas", project_base()
    ).plan
    resultado = ejecutar_plan(plan, {"registros": ENTRADAS})
    return {d: resultado.get(d.lower(), []) for d in DATASETS}


def test_el_espacio_tiene_386_combinaciones_positivas():
    cs = list(combinaciones())
    # Destinos de un dataset cualquiera y pares (hito 240m): cubre l6_13 y l6_23 (B-17).
    assert len(cs) == 386
    assert all(c.rama != "incondicional" or len(c.destinos) == 1 for c in cs)


@pytest.mark.parametrize("c", list(combinaciones()), ids=lambda c: c.nombre)
def test_el_oraculo_coincide_con_el_intérprete(c):
    esperado_ = esperado(c, ENTRADAS)
    obtenido = _interprete(c.programa_sas())
    for d in DATASETS:
        assert _normal(obtenido[d]) == _normal(esperado_[d]), f"{c.nombre} en {d}"


def test_mutar_un_esperado_a_mano_hace_fallar_la_comparacion():
    c = next(x for x in combinaciones() if x.rama == "if_else")
    obtenido = _interprete(c.programa_sas())
    alterado = esperado(c, ENTRADAS)
    alterado[DATASETS[0]][0] = {"ID": "a", "VALOR": 99.0}
    assert any(
        _normal(obtenido[d]) != _normal(alterado[d]) for d in DATASETS
    ), "la mutación del esperado debe romper la comparación"


def test_cada_combinacion_migra_a_jobs_validos_sin_pendiente():
    """Anillo A (B-17 paso 4): cada combinación sale como Jobs que pasan `validar_job`, sin
    pendientes de traducción. Un Job parcial no se escribe (`cli_migrar._validar`)."""
    for c in combinaciones():
        errores = jobs_validos_de(c)
        assert errores == {}, f"{c.nombre}: {errores}"



MUESTRA = "ID,VALOR\na,-1\nb,0\nc,3\nd,5\ne,\n"


def jobs_validos_de(c: Combinacion) -> dict[str, object]:
    """Nombre del Job -> errores de `validar_job`; vacío si todos pasan."""
    plan = compile_file(analyze_program({"p.sas": c.programa_sas()}), "p.sas", project_base()).plan
    plan, _ = plan_desplegado(plan)
    carpeta = Path(tempfile.mkdtemp(prefix="muestra_output_"))
    (carpeta / "REGISTROS.csv").write_text(MUESTRA, encoding="utf-8")
    tablas, _ = esquemas_de_entrada(plan, {}, carpeta)
    errores: dict[str, object] = {}
    for job in plan_a_jobs(plan, tablas).jobs:
        if validar_job(job):
            errores[job.nombre] = validar_job(job)
    return errores


def test_los_negativos_de_destino_repetido_son_las_dos_ramas_independientes():
    """El espacio positivo no tiene dos `IF` independientes: con S1 y S2 como destinos, dos
    `OUTPUT` sin cadena siempre repiten dataset. Esas combinaciones son los casos negativos (B-17)."""
    negs = list(negativos())
    assert len(negs) == 34  # los dos IF sin cadena que repiten dataset, con y sin continuación
    assert all(c.rama == "dos_if_independientes" for c in negs)


@pytest.mark.parametrize("c", list(negativos()), ids=lambda c: c.nombre)
def test_negativo_de_destino_repetido_deja_pendiente_y_ningun_job(c, tmp_path):
    """Anillo A: el destino repetido queda como pendiente con su código estable y no sale ningún
    Job, ni parcial ni completo."""
    programa = tmp_path / "negativo.sas"
    programa.write_text(c.programa_sas(), encoding="utf-8")
    muestra = tmp_path / "muestra"
    muestra.mkdir()
    (muestra / "REGISTROS.csv").write_text(MUESTRA, encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    assert resultado.jobs == []
    assert "P-OUTPUT-DESTINO-REPETIDO" in {p.codigo for p in resultado.pendientes}
