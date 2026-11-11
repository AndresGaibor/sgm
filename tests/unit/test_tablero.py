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
        # hito 98d: job_conciliacion real (tJava; por producto, dos lectores, un tMap y una
        # escritura; más el lector de chequeo, el tJavaRow y el tDie: 3 productos x 4 + 4).
        "job_conciliacion": 16,
        "job_exogena_depositos": 13,
        # hito 84 añade el tMap_normalizacion; hito 87 el tMap_flujos y sus 3 salidas;
        # hito 89 el tMap_cuenta y sus 4 salidas; hito 100d los dos formatos y las dos
        # escrituras de totales.
        "job_producto": 25,
        # hito 97: job_totales real (tJava y una entrada y una salida por archivo: 3 productos
        # x 2 tipos x 2 componentes + tJava).
        "job_totales": 13,
    }
    assert sum(jobs.values()) == 67


def test_conformidad_cuenta_filas_y_secciones():
    datos = tablero.conformidad()
    # Hito 94: sección 2.1 emitida; sus filas X03, X04, X05 y X07 cumplen, X01, X02, X06, X08 y X09
    # no (ver DIFERENCIAS_CONOCIDAS y FILAS_PENDIENTES).
    # Hito 99d: F06 a F08 pasan a diferencias conocidas (16 a 13 cumplidas); 1.2 y 1.3 se emiten.
    assert (datos["filas"], datos["filas_cumplidas"]) == (118, 13)
    assert (datos["secciones"], datos["secciones_emitidas"]) == (22, 5)


def test_pendientes_del_modelo_tienen_motivo(pendientes):
    assert len(pendientes) == 16
    assert all(que and motivo for que, motivo in pendientes)
    assert len({motivo for _, motivo in pendientes}) == 5


def test_corpus_por_nivel_y_estado(datos_corpus):
    assert datos_corpus["casos"] == 131
    assert datos_corpus["por_nivel"]["L6"] == 24
    assert datos_corpus["por_nivel"]["L8"] == 16
    assert sum(datos_corpus["por_nivel"].values()) == 131
    assert sum(datos_corpus["por_estado"].values()) == 131
    assert datos_corpus["con_esperado"] == 129
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
