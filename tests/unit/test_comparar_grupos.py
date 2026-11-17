"""Regresiones de llaves BY, tolerancia e importación del comparador del corpus."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.studio_comparar import comparar_tablas  # noqa: E402


def test_grupo_descendente_en_columna_no_inicial():
    tabla = (["valor", "id"], [["a", "3"], ["b", "2"], ["c", "1"]])

    assert comparar_tablas(tabla, tabla, orden_grupo=[{"columna": "id", "descendente": True}]) == []


def test_varios_by_reordenados_usan_sus_posiciones_locales():
    tabla = (["secundaria", "principal"], [["1", "2"], ["2", "2"], ["1", "1"]])
    orden = [
        {"columna": "principal", "descendente": True},
        {"columna": "secundaria", "descendente": False},
    ]

    assert comparar_tablas(tabla, tabla, orden_grupo=orden) == []
    diferencias = comparar_tablas(
        tabla,
        (tabla[0], [["2", "2"], ["1", "2"], ["1", "1"]]),
        orden_grupo=orden,
    )
    assert [d.tipo for d in diferencias] == ["orden"]


@pytest.mark.parametrize("desfase", [".0", ".005"])
def test_llaves_numericas_equivalentes_respetan_tolerancia(desfase):
    esperada = (["id", "valor"], [["3", "a"], ["2", "b"], ["1", "c"]])
    obtenida = (["id", "valor"], [["3" + desfase, "a"], ["2" + desfase, "b"], ["1" + desfase, "c"]])

    assert (
        comparar_tablas(
            esperada,
            obtenida,
            tolerancia=0.01,
            orden_grupo=[{"columna": "id", "descendente": True}],
        )
        == []
    )


def test_llaves_equivalentes_forman_un_grupo_con_empates_libres():
    esperada = (["id", "valor"], [["3", "a"], ["3.005", "b"], ["2", "c"]])
    obtenida = (["id", "valor"], [["3.0", "b"], ["3.005", "a"], ["2.0", "c"]])

    assert (
        comparar_tablas(
            esperada,
            obtenida,
            tolerancia=0.01,
            orden_grupo=[{"columna": "id", "descendente": True}],
        )
        == []
    )


def test_llaves_equivalentes_no_ocultan_grupo_no_contiguo():
    esperada = (["id", "valor"], [["3", "a"], ["3", "b"], ["2", "c"]])
    obtenida = (["id", "valor"], [["3.0", "a"], ["2.0", "c"], ["3.005", "b"]])

    diferencias = comparar_tablas(
        esperada,
        obtenida,
        tolerancia=0.01,
        orden_grupo=[{"columna": "id", "descendente": True}],
    )

    assert [d.tipo for d in diferencias] == ["orden", "orden"]
    assert "separadas" in diferencias[0].mensaje


def test_llaves_equivalentes_conservan_orden_de_grupos():
    esperada = (["id"], [["3"], ["2"], ["1"]])
    obtenida = (["id"], [["2.0"], ["3.0"], ["1.0"]])

    diferencias = comparar_tablas(
        esperada,
        obtenida,
        tolerancia=0.01,
        orden_grupo=[{"columna": "id", "descendente": True}],
    )

    assert [d.tipo for d in diferencias] == ["orden"]


def test_llaves_fuera_de_tolerancia_siguen_siendo_grupos_distintos():
    diferencias = comparar_tablas(
        (["id"], [["3"]]),
        (["id"], [["3.02"]]),
        tolerancia=0.01,
        orden_grupo=[{"columna": "id", "descendente": True}],
    )

    assert [d.tipo for d in diferencias] == ["orden", "faltante", "sobrante"]


def test_varios_by_reordenados_comparan_todas_las_llaves_con_tolerancia():
    esperada = (
        ["secundaria", "valor", "principal"],
        [["1", "a", "3"], ["1", "b", "3"], ["2", "c", "3"], ["1", "d", "2"]],
    )
    obtenida = (
        esperada[0],
        [
            ["1.005", "b", "3.0"],
            ["1.0", "a", "3.005"],
            ["2.005", "c", "3.0"],
            ["1.0", "d", "2.005"],
        ],
    )
    orden = [
        {"columna": "principal", "descendente": True},
        {"columna": "secundaria", "descendente": False},
    ]

    assert comparar_tablas(esperada, obtenida, tolerancia=0.01, orden_grupo=orden) == []
    diferencias = comparar_tablas(
        esperada,
        (obtenida[0], [obtenida[1][2], *obtenida[1][:2], obtenida[1][3]]),
        tolerancia=0.01,
        orden_grupo=orden,
    )
    assert [d.tipo for d in diferencias] == ["orden"]


def test_comparador_importa_desde_raiz_en_proceso_limpio():
    entorno = {k: v for k, v in os.environ.items() if k.upper() != "PYTHONPATH"}
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            "from tools.corpus_lib.studio_comparar import "
            "comparar_archivos; print(comparar_archivos.__name__)",
        ],
        cwd=REPO,
        env=entorno,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "comparar_archivos"


@pytest.mark.parametrize("descendente", [False, True])
def test_intervalos_solapados_conservan_grupos_independientes(descendente):
    esperada = (["id", "valor"], [["1", "a"], ["1.018", "b"]])
    obtenida = (["id", "valor"], [["0.991", "a"], ["1.009", "b"]])
    if descendente:
        esperada[1].reverse()
        obtenida[1].reverse()

    assert comparar_tablas(esperada, obtenida, tolerancia=0.01, orden_relevante=True) == []
    assert comparar_tablas(
        esperada,
        obtenida,
        tolerancia=0.01,
        orden_grupo=[{"columna": "id", "descendente": descendente}],
    ) == []
