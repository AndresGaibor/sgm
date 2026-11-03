"""Reglas semánticas de PROC SQL, leídas de `rules/sas/sql-semantica.yaml`.

El lowering de PROC SQL y el generador de SQL de base consultan este módulo; ninguno decide por su
cuenta qué hacer con un agregado sin GROUP BY o con un SELECT INTO. Los tratamientos son:
- `pendiente`: la sentencia queda parcial con su nota; el generador de SQL no la escribe.
- `programa_anfitrion`: el valor va a una macro variable del programa, como operador set_variable.

Un id que el código no conoce, o un tratamiento fuera de la lista, hace fallar la carga: así un
cambio en el YAML no se aplica en silencio.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[3]
SEMANTICA_PATH = ROOT_DIR / "rules" / "sas" / "sql-semantica.yaml"

AGREGADO = "agregado-sin-group-by"
SELECT_INTO = "select-into-macrovariable"
IDS_CONOCIDOS = frozenset({AGREGADO, SELECT_INTO})
TRATAMIENTOS = frozenset({"pendiente", "programa_anfitrion"})


@dataclass(frozen=True)
class Regla:
    id: str
    tratamiento: str
    etiqueta: str
    descripcion: str


def cargar(path: Path = SEMANTICA_PATH) -> dict[str, Regla]:
    """Reglas del YAML por id. Lanza `ValueError` si un id o un tratamiento no es válido."""
    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    reglas: dict[str, Regla] = {}
    for entrada in data.get("reglas", []):
        rid = str(entrada.get("id", ""))
        if rid not in IDS_CONOCIDOS:
            raise ValueError(f"regla SQL desconocida en {path.name}: {rid!r}")
        tratamiento = str(entrada.get("tratamiento", ""))
        if tratamiento not in TRATAMIENTOS:
            raise ValueError(f"tratamiento no válido para {rid!r}: {tratamiento!r}")
        reglas[rid] = Regla(
            id=rid,
            tratamiento=tratamiento,
            etiqueta=str(entrada.get("etiqueta") or ""),
            descripcion=" ".join(str(entrada.get("descripcion", "")).split()),
        )
    faltan = IDS_CONOCIDOS - reglas.keys()
    if faltan:
        raise ValueError(f"faltan reglas SQL en {path.name}: {sorted(faltan)}")
    return reglas


@lru_cache(maxsize=1)
def reglas() -> dict[str, Regla]:
    return cargar()


def tratamiento(rid: str) -> str:
    return reglas()[rid].tratamiento


def aggregate_pendiente(params: dict[str, Any]) -> bool:
    """El agregado lleva columnas sin agrupar y la regla dice que queda pendiente."""
    return bool(params.get("pendiente")) and tratamiento(AGREGADO) == "pendiente"
