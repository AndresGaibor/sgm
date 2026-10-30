"""Catálogo de componentes de Talend copiado en `rules/talend/`, fuente única de la compilación."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMPONENTS = ROOT / "rules" / "talend" / "components.json"
INVENTORY = ROOT / "rules" / "talend" / "official-component-inventory.json"


@cache
def component_names() -> frozenset[str]:
    """Nombres de componentes conocidos: los del catálogo y los del inventario oficial."""
    components = json.loads(COMPONENTS.read_text(encoding="utf-8"))["components"]
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))["components"]
    return frozenset(components) | {entry["name"] for entry in inventory}
