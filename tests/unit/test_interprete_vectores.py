"""Adaptación y cruce de los vectores semánticos con el intérprete."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import corpus_semantica as cs  # noqa: E402

from sgm.migrar.interprete import _arbol, _valor  # noqa: E402
from sgm.migrar.interprete_vectores import evaluar_vector  # noqa: E402
from tools.funciones_inventario import inventario, resumen  # noqa: E402


def test_adapta_scan_al_interprete() -> None:
    assert evaluar_vector("scan", ["a b c", 2]) == "b"


def test_adapta_input_con_w_y_d() -> None:
    assert evaluar_vector("input", ["23.0", 6, 2]) == 23.0
    assert evaluar_vector("input", ["0023", 6, 2]) == 0.23
    assert evaluar_vector("input", ["1", 8, 10]) == 1e-10


def test_input_en_expresion_conserva_el_informat_literal() -> None:
    assert _valor(_arbol("INPUT('1234567', 3.0)"), {}) == 123.0
    assert _valor(_arbol("INPUT('1', 8.10)"), {}) == 1e-10
    assert _valor(_arbol("INPUT('1E3', 8.2)"), {}) == 1000.0


def test_adapta_comparacion_con_faltante() -> None:
    assert evaluar_vector("cmp", [None, "<", 500]) is True


def test_adapta_es_missing_para_texto_en_blanco() -> None:
    assert evaluar_vector("is_missing", ["   "]) is True


def test_concat_trata_los_argumentos_como_literales() -> None:
    assert evaluar_vector("concat", ["x' || 'y", "z"]) == "x' || 'yz"


def test_interprete_ejecuta_y_coincide_con_todos_los_vectores_conocidos() -> None:
    resultado = cs.verificar(motor="interprete")
    esperados = Counter(
        v["funcion"]
        for v in cs.cargar_vectores()
        if v["confianza"] in ("documentado", "deducido")
    )

    assert resultado["fallos"] == []
    assert resultado["diferencias_motores"] == []
    assert resultado["ejecuciones_por_funcion"] == dict(esperados)


def test_inventario_recibe_los_conteos_reales_del_interprete() -> None:
    ejecucion = cs.verificar(motor="interprete")
    total = resumen(inventario(REPO), ejecucion["ejecuciones_por_funcion"])

    assert total["vectores_en_interprete"] == 125


def test_verificar_identifica_vector_que_difiere_del_oraculo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "vectores.yaml"
    ruta.write_text(
        'vectores:\n'
        '  - id: scan-diferente\n'
        '    funcion: scan\n'
        '    entrada: ["a b c", 2]\n'
        '    esperado: "b"\n'
        '    confianza: documentado\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(cs, "evaluar_vector", lambda funcion, entrada: "resultado distinto")

    resultado = cs.verificar(ruta, motor="interprete")

    assert resultado["fallos"]
    assert resultado["fallos"][0]["id"] == "scan-diferente"
    assert resultado["diferencias_motores"][0]["id"] == "scan-diferente"
