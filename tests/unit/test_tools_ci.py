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
import validacion  # noqa: E402


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


def test_el_cierre_termina_en_cero_si_todo_pasa(monkeypatch, capsys):
    # Los pasos se sustituyen por comandos triviales, como pide el encabezado de este archivo.
    # Correr los de verdad dentro de la suite significa un `pytest -n0` anidado sobre los mismos
    # archivos que la suite ya está corriendo, y la limpieza de temporales de ese pytest anidado
    # tropieza con el guardia de borrado masivo del entorno: el paso sale distinto de cero por un
    # motivo que no tiene que ver con el proyecto. Lo que esta prueba mide es la composición del
    # cierre y su código de salida; los pasos de verdad los cubren la suite, `ruff` y las pruebas
    # del oráculo.
    triviales = [
        ci.Paso("uno", (sys.executable, "-c", "pass")),
        ci.Paso("dos", (sys.executable, "-c", "print('hola')")),
    ]
    monkeypatch.setattr(ci, "pasos", lambda con_suite, con_tablero: triviales)
    codigo = ci.main(["--sin-suite", "--sin-tablero", "--sin-registro"])
    salida = capsys.readouterr().out
    # El informe va en el mensaje: si un paso falla, el fallo tiene que decir cuál y por qué.
    assert codigo == 0, salida
    assert "Todo verde." in salida
    assert "| uno | OK |" in salida


def test_el_cierre_en_verde_deja_el_estado_para_el_commit(tmp_path):
    resultados = [
        ci.Resultado(ci.Paso("ruff", ()), 0, 0.1, "All checks passed"),
        ci.Resultado(ci.Paso("suite", ()), 0, 0.1, "3128 passed"),
        ci.Resultado(ci.Paso("cruces del corpus", ()), 0, 0.1, ""),
        ci.Resultado(ci.Paso("oráculo del corpus", ()), 0, 0.1, ""),
    ]

    ci.registrar_cierre(resultados, con_suite=True, base=tmp_path, huella="prueba")

    estado = validacion.leer_estado(tmp_path)
    assert estado["pasos"]["pytest"]["ok"] is True
    assert estado["pasos"]["ruff"]["ok"] is True
    assert estado["pasos"]["ci"]["ok"] is True


def test_un_cierre_sin_suite_no_autoriza_el_commit(tmp_path):
    resultados = [
        ci.Resultado(ci.Paso("ruff", ()), 0, 0.1, "All checks passed"),
        ci.Resultado(ci.Paso("cruces del corpus", ()), 0, 0.1, ""),
    ]

    ci.registrar_cierre(resultados, con_suite=False, base=tmp_path, huella="prueba")

    estado = validacion.leer_estado(tmp_path)
    assert "ci" not in estado["pasos"]
    assert "pytest" not in estado["pasos"]


def test_un_paso_rojo_deja_el_cierre_en_falla(tmp_path):
    resultados = [
        ci.Resultado(ci.Paso("ruff", ()), 0, 0.1, "All checks passed"),
        ci.Resultado(ci.Paso("suite", ()), 1, 0.1, "2 failed, 3 passed"),
    ]

    ci.registrar_cierre(resultados, con_suite=True, base=tmp_path, huella="prueba")

    estado = validacion.leer_estado(tmp_path)
    assert estado["pasos"]["ci"]["ok"] is False
    assert "suite" in estado["pasos"]["ci"]["resumen"]
