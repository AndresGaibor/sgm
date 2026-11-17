"""Aislamiento común de las pruebas y reparto de workers de `xdist`.

Sin la base aislada, `sgm compile`, `sgm decisions` o `sgm gaps` usan `~/.sgm/sgm.sqlite`. Ese
archivo lo comparten todas las pruebas, todos los workers de xdist y todas las ejecuciones previas:
una decisión guardada por una prueba cambiaba la salida de otra. Cada prueba recibe su propia base
temporal; una prueba que necesite otra la fija con su propio `monkeypatch.setenv("SGM_DB", ...)`.

`addopts` trae `-n auto`. Levantar dieciséis procesos para correr un archivo cuesta más que el
archivo: cuando la selección es de pocos módulos, esta prueba corre en serie.
"""

from __future__ import annotations

from pathlib import Path

import pytest

#: Número de módulos de prueba a partir del cual vale la pena repartir el trabajo entre procesos.
MODULOS_PARA_PARALELO = 8


@pytest.fixture(autouse=True)
def sgm_db_aislada(tmp_path, monkeypatch):
    """Apunta `SGM_DB` a una base temporal por prueba."""
    monkeypatch.setenv("SGM_DB", str(tmp_path / "sgm-test.sqlite"))


def _n_pedido_en_la_linea(config: pytest.Config) -> bool:
    """Si el usuario pidió `-n`/`--numprocesses` en la línea de comandos, se respeta."""
    for arg in config.invocation_params.args:
        if arg == "--numprocesses" or arg.startswith("--numprocesses="):
            return True
        if arg == "-n" or (arg.startswith("-n") and not arg.startswith("-no")):
            return True
    return False


def _modulos_seleccionados(arg: str) -> int:
    """Módulos de prueba que abarca un argumento: uno si es archivo, todos si es carpeta."""
    ruta = Path(arg.split("::")[0])
    if ruta.is_file():
        return 1
    if not ruta.is_dir():
        return 0
    return sum(1 for _ in ruta.rglob("test_*.py"))


def pytest_configure(config: pytest.Config) -> None:
    """Corre en serie cuando la selección es de pocos módulos, aunque `addopts` pida `-n auto`."""
    if config.option.numprocesses in (None, 0) or _n_pedido_en_la_linea(config):
        return
    modulos = sum(_modulos_seleccionados(arg) for arg in config.args)
    if modulos and modulos <= MODULOS_PARA_PARALELO:
        config.option.numprocesses = 0
        config.option.dist = "no"
        config.option.tx = []
