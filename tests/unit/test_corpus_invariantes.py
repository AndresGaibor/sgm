"""Invariantes de los casos del corpus, y pruebas del analizador de invariantes.

La prueba genérica recorre todos los casos que declaran `invariantes` en su `caso.yaml` y las evalúa
sobre los CSV de `esperado/`, `entradas/` y `entradas_preparadas/`. Un caso nuevo con invariantes entra
solo, sin tocar esta prueba.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import todos_los_casos  # noqa: E402
from corpus_lib.invariantes import analizar, comprobar  # noqa: E402

CORPUS = REPO / "tests" / "corpus"
CASOS_CON_INVARIANTES = [caso for caso in todos_los_casos(CORPUS) if caso.invariantes]


@pytest.mark.parametrize("caso", CASOS_CON_INVARIANTES, ids=lambda caso: caso.nombre)
def test_invariantes_del_caso_se_cumplen(caso):
    carpetas = [caso.esperado, caso.entradas, caso.entradas_preparadas]
    assert comprobar(list(caso.invariantes), carpetas, caso.tolerancia) == []


def test_hay_casos_de_capa_a_con_invariantes_en_l2_y_l3():
    niveles = {caso.nivel for caso in CASOS_CON_INVARIANTES}
    assert {"L2", "L3"} <= niveles


def _csv(carpeta: Path, nombre: str, texto: str) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"{nombre}.csv").write_text(texto, encoding="utf-8")
    return carpeta


def test_analizar_acepta_la_gramatica_completa():
    izquierda, operador, derecha = analizar("valor(t.a) + filas(t) - 2 <= suma(t.b)")
    assert operador == "<="
    assert izquierda[0] == "-"
    assert derecha == ("suma", "t", "b")


@pytest.mark.parametrize(
    "texto",
    [
        "filas(t) 3",  # falta el operador
        "filas(t) == ",  # termina antes de tiempo
        "suma(t) == 1",  # falta el nombre de columna
        "media(t.a) == 1",  # función desconocida
        "filas(t) = 1",  # un solo signo igual
        "filas(t) == 1 extra",  # sobra texto
        "filas(t) == 1 % 2",  # carácter no reconocido
    ],
)
def test_analizar_rechaza_textos_mal_formados(texto):
    with pytest.raises(ValueError):
        analizar(texto)


def test_comprobar_suma_y_cuenta_con_tolerancia(tmp_path):
    carpeta = _csv(tmp_path, "t", "a,b\n1,x\n2.5,\n,y\n")
    assert comprobar(["filas(t) == 3", "suma(t.a) == 3.5"], [carpeta], 0) == []
    fallos = comprobar(["suma(t.a) == 4"], [carpeta], 0.4)
    assert len(fallos) == 1 and "no se cumple" in fallos[0]
    assert comprobar(["suma(t.a) == 4"], [carpeta], 0.5) == []


def test_valor_toma_la_primera_fila_y_falla_si_esta_vacia(tmp_path):
    carpeta = _csv(tmp_path, "r", "total\n,\n5\n")
    fallos = comprobar(["valor(r.total) == 5"], [carpeta], 0)
    assert fallos and "vacía" in fallos[0]


def test_tabla_inexistente_se_reporta_sin_romper(tmp_path):
    fallos = comprobar(["filas(no_existe) == 1"], [tmp_path], 0)
    assert fallos and "no se pudo evaluar" in fallos[0]


def test_la_primera_carpeta_con_la_tabla_gana(tmp_path):
    esperado = _csv(tmp_path / "esperado", "t", "a\n1\n")
    entradas = _csv(tmp_path / "entradas", "t", "a\n1\n2\n")
    assert comprobar(["filas(t) == 1"], [esperado, entradas], 0) == []
    assert comprobar(["filas(t) == 2"], [esperado, entradas], 0) != []
