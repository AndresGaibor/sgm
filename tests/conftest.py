"""Aislamiento común de las pruebas: ninguna prueba escribe en la base del usuario.

Sin esto, `sgm compile`, `sgm decisions` o `sgm gaps` usan `~/.sgm/sgm.sqlite`. Ese archivo lo
comparten todas las pruebas, todos los workers de xdist y todas las ejecuciones previas: una
decisión guardada por una prueba cambiaba la salida de otra. Cada prueba recibe su propia base
temporal; una prueba que necesite otra la fija con su propio `monkeypatch.setenv("SGM_DB", ...)`.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def sgm_db_aislada(tmp_path, monkeypatch):
    """Apunta `SGM_DB` a una base temporal por prueba."""
    monkeypatch.setenv("SGM_DB", str(tmp_path / "sgm-test.sqlite"))
