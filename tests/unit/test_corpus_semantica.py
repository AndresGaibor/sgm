"""Pruebas de la implementación de referencia de funciones SAS (capa B del oráculo).

Cada vector de `tests/corpus/semantica/vectores.yaml` documentado o deducido debe pasar.
Los `incierto` se reportan aparte y no cuentan como fallo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import corpus_semantica as cs  # noqa: E402

VECTORES = cs.cargar_vectores()
PROBADOS = [v for v in VECTORES if v["confianza"] in ("documentado", "deducido")]
CAMPOS = {"id", "funcion", "entrada", "esperado", "fuente_url", "cita", "confianza"}


@pytest.mark.parametrize("vector", PROBADOS, ids=lambda v: v["id"])
def test_vector_documentado_o_deducido_pasa(vector: dict) -> None:
    obtenido = cs.ejecutar_vector(vector)
    assert cs._coincide(obtenido, vector["esperado"]), (
        f"{vector['id']}: esperado {vector['esperado']!r}, obtenido {obtenido!r}"
    )


def test_hay_suficientes_vectores() -> None:
    documentados = [v for v in VECTORES if v["confianza"] == "documentado"]
    assert len(VECTORES) >= 60
    assert len(documentados) >= 25


def test_cada_vector_tiene_campos_y_fuente() -> None:
    for vector in VECTORES:
        assert CAMPOS <= set(vector), f"campos incompletos en {vector.get('id')}"
        assert vector["confianza"] in cs.CONFIANZAS
        if vector["confianza"] == "incierto":
            assert vector["fuente_url"] == "ninguna"
            continue
        assert vector["fuente_url"].startswith("https://support.sas.com/"), vector["id"]
        assert 0 < len(vector["cita"].split()) <= 25, vector["id"]


def test_incierto_no_cuenta_como_fallo() -> None:
    resultado = cs.verificar()
    assert resultado["fallos"] == []
    assert len(resultado["inciertos"]) >= 1


def test_faltante_es_unico_y_menor_que_cualquier_numero() -> None:
    assert cs.Faltante() is cs.FALTANTE
    assert cs.cmp(cs.FALTANTE, "<", -1e9) is True
    assert cs.cmp(-1e9, ">", cs.FALTANTE) is True


def test_scan_fuera_de_rango_da_un_blanco() -> None:
    assert cs.evaluar("scan", "ab cd", 3) == " "


def test_round_empate_va_al_de_mayor_valor_absoluto() -> None:
    assert cs.evaluar("round", 0.5) == 1
    assert cs.evaluar("round", -0.5) == -1


def test_input_con_punto_decimal_ignora_d() -> None:
    assert cs.evaluar("input", "1.5", 8, 3) == 1.5


def test_linea_no_valida_del_yaml_se_rechaza(tmp_path: Path) -> None:
    ruta = tmp_path / "malo.yaml"
    ruta.write_text("vectores:\nlinea suelta sin guion\n", encoding="utf-8")
    with pytest.raises(ValueError):
        cs.cargar_vectores(ruta)


def test_cli_verificar_sale_con_cero() -> None:
    assert cs.main(["verificar"]) == 0
