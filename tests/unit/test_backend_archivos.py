"""Backend de archivos: escribe el par `.item`/`.properties` y no compila ni ejecuta."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from sgm.backend_talend import ArchivosBackend, BackendNoDisponible, ResultadoLote
from sgm.talend_item.modelo import Job


def test_escribir_devuelve_un_item_y_un_properties_por_job(tmp_path):
    rutas = ArchivosBackend().escribir([Job(nombre="a"), Job(nombre="b")], tmp_path)

    assert len(rutas) == 4
    assert all(ruta.exists() for ruta in rutas)
    assert sorted(ruta.name for ruta in rutas) == [
        "a_0.1.item",
        "a_0.1.properties",
        "b_0.1.item",
        "b_0.1.properties",
    ]


def test_compilar_lote_no_esta_disponible(tmp_path):
    with pytest.raises(BackendNoDisponible):
        ArchivosBackend().compilar_lote(["a"])


def test_verificar_no_esta_disponible():
    with pytest.raises(BackendNoDisponible):
        ArchivosBackend().verificar("a", {})


def test_resultado_lote_es_inmutable():
    resultado = ResultadoLote(compilan=("a",), no_compilan={})

    with pytest.raises(FrozenInstanceError):
        resultado.compilan = ()
