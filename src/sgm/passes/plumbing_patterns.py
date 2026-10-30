"""Patrones de fontanería de SAS que no se migran a Talend, como datos (F1.4).

Fontanería es lo que sirve al propio SAS para orquestar, esperar, medir o limpiar: shell auxiliar,
sondeo de procesos, mensajes, tiempos, variables de control, borrado de temporales, troceo por lotes.
Talend resuelve esas necesidades con otros mecanismos (triggers, tStatCatcher, tDie, Batch size).

Los patrones viven en `rules/sas/plumbing.yaml`. Este módulo solo los carga. La pasada
`p02_plumbing` los aplica al texto de cada paso y registra cada coincidencia en `plan.not_migrated`
con su equivalente. La clasificación es por FORMA (qué hace la operación), no por el nombre de la
macro que la contiene.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PLUMBING_YAML = ROOT / "rules" / "sas" / "plumbing.yaml"
_BANDERAS = {"i": re.IGNORECASE}


@dataclass(frozen=True)
class PlumbingPattern:
    category: str
    what: str
    reason: str
    talend: str
    pattern: re.Pattern[str]


def cargar(path: Path = PLUMBING_YAML) -> tuple[PlumbingPattern, ...]:
    """Patrones de `plumbing.yaml`, en el orden del archivo (el primero que coincide gana)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    patrones = []
    for entrada in data["entries"]:
        banderas = 0
        for letra in entrada.get("flags", []):
            banderas |= _BANDERAS[letra]
        patrones.append(
            PlumbingPattern(
                category=entrada["id"],
                what=entrada["what"],
                reason=entrada["reason"],
                talend=entrada["talend"],
                pattern=re.compile(entrada["pattern"], banderas),
            )
        )
    return tuple(patrones)


PLUMBING_PATTERNS: tuple[PlumbingPattern, ...] = cargar()


def match_plumbing(statement: str) -> PlumbingPattern | None:
    """Primer patrón de fontanería que coincide con el texto de un paso, o None."""
    return next((p for p in PLUMBING_PATTERNS if p.pattern.search(statement)), None)
