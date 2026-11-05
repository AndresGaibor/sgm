"""Tablero: las medidas de la sección 2 del plan, calculadas sin Studio.

El tablero emite los Jobs del programa grande y compara la referencia manual con el diseño emitido;
las pruebas fijan esas cifras para que un cambio de emisor que mueva la línea base se vea.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import tablero  # noqa: E402

PROGRAMA = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
CORPUS = REPO / "tests" / "corpus"


@pytest.fixture(scope="module")
def jobs() -> dict[str, int]:
    return tablero.componentes(PROGRAMA)


@pytest.fixture(scope="module")
def pendientes() -> list[tuple[str, str]]:
    return tablero.pendientes(PROGRAMA)


@pytest.fixture(scope="module")
def datos_corpus() -> dict:
    return tablero.corpus(CORPUS)


def test_componentes_por_job_del_programa_grande(jobs):
    assert jobs == {
        "job_conciliacion": 1,
        "job_exogena_depositos": 13,
        # hito 84 añade el tMap_normalizacion; hito 87 el tMap_flujos y sus 3 salidas.
        "job_producto": 16,
        "job_totales": 1,
    }
    assert sum(jobs.values()) == 31


def test_conformidad_cuenta_filas_y_secciones():
    datos = tablero.conformidad()
    assert (datos["filas"], datos["filas_cumplidas"]) == (118, 12)
    assert (datos["secciones"], datos["secciones_emitidas"]) == (22, 2)


def test_pendientes_del_modelo_tienen_motivo(pendientes):
    assert len(pendientes) == 16
    assert all(que and motivo for que, motivo in pendientes)
    assert len({motivo for _, motivo in pendientes}) == 5


def test_corpus_por_nivel_y_estado(datos_corpus):
    assert datos_corpus["casos"] == 117
    assert datos_corpus["por_nivel"]["L8"] == 16
    assert sum(datos_corpus["por_nivel"].values()) == 117
    assert sum(datos_corpus["por_estado"].values()) == 117
    assert datos_corpus["con_esperado"] == 116
    assert datos_corpus["construcciones"] > datos_corpus["construcciones_traducibles"] > 0


def test_la_tabla_tiene_encabezado_y_una_fila_por_medida():
    filas = tablero.filas_tablero(PROGRAMA, CORPUS, con_suite=False)
    texto = tablero.tabla(filas)
    assert texto.startswith("| Medida | Valor |\n|---|---|\n")
    assert len(texto.strip().splitlines()) == len(filas) + 2
    assert "no hay traductor general" in texto


def test_el_tablero_imprime_la_tabla_y_los_motivos(capsys):
    assert tablero.main(["--markdown"]) == 0
    salida = capsys.readouterr().out
    assert "| Componentes emitidos por" in salida
    assert "Pendientes por motivo" not in salida
    assert tablero.main([]) == 0
    assert "Pendientes por motivo" in capsys.readouterr().out
