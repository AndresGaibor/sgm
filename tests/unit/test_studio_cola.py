"""Cola de validaciones pendientes de Studio: agrega, reintenta y se escribe sin dejar restos."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))

from corpus_lib.studio_cola import Pendiente, encolar, leer, vaciar  # noqa: E402


def test_encolar_dos_casos_y_leerlos(tmp_path):
    ruta = tmp_path / "out" / "studio-pendientes.json"

    encolar(ruta, Pendiente("L6/l6_18_output_condicional", "BRIDGE_DEAD"))
    encolar(ruta, Pendiente("L6/l6_22_output_else_if", "MODAL_BLOCKING"))

    pendientes = leer(ruta)
    assert [p.caso for p in pendientes] == [
        "L6/l6_18_output_condicional",
        "L6/l6_22_output_else_if",
    ]
    assert [p.motivo for p in pendientes] == ["BRIDGE_DEAD", "MODAL_BLOCKING"]
    assert all(p.intentos == 1 for p in pendientes)


def test_encolar_el_mismo_caso_suma_intento_sin_duplicar(tmp_path):
    ruta = tmp_path / "cola.json"

    encolar(ruta, Pendiente("L6/l6_18_output_condicional", "BRIDGE_DEAD"))
    encolar(ruta, Pendiente("L6/l6_18_output_condicional", "STUDIO_BUSY"))

    pendientes = leer(ruta)
    assert len(pendientes) == 1
    assert pendientes[0].intentos == 2
    assert pendientes[0].motivo == "STUDIO_BUSY"


def test_vaciar_quita_solo_el_resuelto(tmp_path):
    ruta = tmp_path / "cola.json"
    encolar(ruta, Pendiente("a", "BRIDGE_DEAD"))
    encolar(ruta, Pendiente("b", "BUSY"))
    encolar(ruta, Pendiente("c", "MODAL_BLOCKING"))

    vaciar(ruta, {"b"})

    assert [p.caso for p in leer(ruta)] == ["a", "c"]


def test_leer_un_archivo_corrupto_devuelve_lista_vacia_sin_lanzar(tmp_path):
    ruta = tmp_path / "cola.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")

    assert leer(ruta) == []


def test_encolar_es_atomico_y_no_deja_el_temporal(tmp_path):
    ruta = tmp_path / "cola.json"

    encolar(ruta, Pendiente("a", "BRIDGE_DEAD"))

    assert sorted(p.name for p in tmp_path.iterdir()) == ["cola.json"]
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos == [{"caso": "a", "motivo": "BRIDGE_DEAD", "intentos": 1}]


def test_leer_una_cola_inexistente_devuelve_lista_vacia(tmp_path):
    assert leer(tmp_path / "no-existe.json") == []
