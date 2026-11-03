"""Las reglas de semántica de PROC SQL tienen forma válida y un tratamiento conocido."""

from __future__ import annotations

from pathlib import Path

import yaml

RUTA = Path(__file__).resolve().parents[2] / "rules" / "sas" / "sql-semantica.yaml"
TRATAMIENTOS = {"portable", "pendiente", "reconstruir_en_anfitrion", "advertencia"}
CAMPOS = {"id", "detecta", "en_sas", "tratamiento", "motivo", "fuente"}


def test_cada_regla_tiene_campos_y_tratamiento_conocido() -> None:
    reglas = yaml.safe_load(RUTA.read_text(encoding="utf-8"))["reglas"]
    assert reglas
    ids = [r["id"] for r in reglas]
    assert len(ids) == len(set(ids))
    for regla in reglas:
        assert CAMPOS <= set(regla), regla.get("id")
        assert regla["tratamiento"] in TRATAMIENTOS, regla["id"]
        assert regla["fuente"].startswith("https://"), regla["id"]
