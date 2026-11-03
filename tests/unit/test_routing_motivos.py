"""Cada motivo de hueco de `rules/routing.yaml` tiene dueño y aparece en el código.

Un motivo sin uso en `src/sgm` es un dueño asignado a nada: esta prueba lo marca para decidir si
se borra o se implementa. Hoy no hay ninguno.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
ROUTING = REPO / "rules" / "routing.yaml"


def _motivos() -> list[str]:
    datos = yaml.safe_load(ROUTING.read_text(encoding="utf-8"))
    return sorted(datos["owners"])


def _codigo() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in (REPO / "src" / "sgm").rglob("*.py"))


def test_cada_motivo_tiene_dueno_y_aparece_en_el_codigo():
    codigo = _codigo()
    sin_uso = [m for m in _motivos() if m not in codigo]
    assert sin_uso == [], f"motivos sin uso en src/sgm: {sin_uso}"


def test_cada_motivo_tiene_un_dueno_con_nombre():
    datos = yaml.safe_load(ROUTING.read_text(encoding="utf-8"))
    vacios = [m for m, dueno in datos["owners"].items() if not str(dueno).strip()]
    assert vacios == []
