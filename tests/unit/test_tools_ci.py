"""Cierre de hito en un comando: composición de los pasos, informe y código de salida.

No corre la suite (sería correr pytest dentro de pytest): los pasos se prueban con comandos
triviales, que es lo que decide si el cierre falla y qué imprime.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import ci  # noqa: E402


def test_los_pasos_incluyen_ruff_suite_cruces_oraculo_y_tablero():
    nombres = [paso.nombre for paso in ci.pasos(con_suite=True, con_tablero=True)]
    assert nombres == [
        "ruff",
        "suite",
        "cruces del corpus",
        "oráculo del corpus",
        "tablero",
    ]
    opcionales = [paso.nombre for paso in ci.pasos(True, True) if not paso.obligatorio]
    assert opcionales == ["tablero"]


def test_sin_suite_ni_tablero_quedan_las_comprobaciones_rapidas():
    nombres = [paso.nombre for paso in ci.pasos(con_suite=False, con_tablero=False)]
    assert nombres == ["ruff", "cruces del corpus", "oráculo del corpus"]


def test_un_paso_que_falla_marca_falla_y_rompe_el_cierre():
    resultado = ci.ejecutar(ci.Paso("falla", (sys.executable, "-c", "import sys; sys.exit(3)")))
    assert (resultado.codigo, resultado.marca, resultado.ok) == (3, "FALLA", False)


def test_un_paso_informativo_que_falla_solo_avisa():
    paso = ci.Paso("aviso", (sys.executable, "-c", "import sys; sys.exit(1)"), obligatorio=False)
    resultado = ci.ejecutar(paso)
    assert (resultado.marca, resultado.ok) == ("aviso", True)


def test_la_cola_de_salida_esta_en_el_informe():
    paso = ci.Paso("habla", (sys.executable, "-c", "print('hola desde el paso')"))
    resultado = ci.ejecutar(paso)
    assert resultado.salida == "hola desde el paso"
    assert resultado.marca == "OK"
    tabla = ci.informe([resultado])
    assert "| habla | OK |" in tabla


def test_ruff_se_resuelve_en_el_entorno_de_uv():
    assert ci._comando(("ruff", "check", "."))[0].endswith("ruff")
    assert ci._comando((sys.executable, "-m", "pytest"))[0] == sys.executable


def test_el_cierre_termina_en_cero_si_todo_pasa(capsys):
    assert ci.main(["--sin-suite", "--sin-tablero"]) == 0
    salida = capsys.readouterr().out
    assert "Todo verde." in salida
