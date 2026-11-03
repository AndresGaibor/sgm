"""Fase 3.1 y 3.2 de `docs/automatizacion/03-plan-produccion.md`: campos por valor y pendientes.

Todo valor del plan con componente trae fuente, regla y confianza. Todo pendiente tiene valor
nulo, motivo, dueño y cómo se cierra: nada se inventa en silencio.
"""

from __future__ import annotations

from pathlib import Path

from sgm.compile import compile_project
from sgm.emit.plan_json import plan_to_dict

ROOT = Path(__file__).resolve().parents[2]
PROGRAMAS = [
    ROOT / "tests" / "fixtures" / "sas" / "p0_ejemplo_basico.sas",
    ROOT / "tests" / "fixtures" / "sas" / "p1_merge_first_last.sas",
]


def _planes():
    for ruta in PROGRAMAS:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        compilados, _ = compile_project({ruta.name: texto})
        yield plan_to_dict(compilados[ruta.name].plan)


def test_cada_componente_tiene_fuente_regla_y_confianza() -> None:
    for plan in _planes():
        for op in plan["operators"]:
            valor = op["valor_componente"]
            if valor is None:
                continue
            assert valor["fuente"], op["id"]
            assert valor["regla"].count("@") == 1, op["id"]
            assert valor["confianza"] in ("alta", "media", "baja"), op["id"]


def test_cada_pendiente_tiene_dueno_y_como_cerrarse() -> None:
    for plan in _planes():
        for fila in plan["pendientes"]:
            assert fila["valor"] is None
            pendiente = fila["pendiente"]
            assert pendiente["motivo"], fila
            assert pendiente["dueno"], fila
            assert pendiente["se_cierra_con"], fila
