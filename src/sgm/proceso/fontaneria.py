"""Sección 6 del diseño: qué del SAS es fontanería y cuál es su equivalente en Talend.

Aplica los patrones de `rules/sas/plumbing.yaml` a cada sentencia del programa ya expandido. La
clave de cada fila es lo que hace el patrón y el valor es el texto `talend:` de la regla, con el
número de sentencias que casaron. Es lo que el SAS demuestra: no se inventa ningún equivalente.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from sgm.frontend.program import ProgramItem
from sgm.passes.plumbing_patterns import match_plumbing


@dataclass(frozen=True)
class Equivalencia:
    categoria: str
    que: str
    talend: str
    cantidad: int


def _texto(item: ProgramItem) -> str:
    obj = item.item
    return getattr(obj, "text", "") or getattr(obj, "command", "") or ""


def contar_fontaneria(items: list[ProgramItem]) -> list[Equivalencia]:
    """Equivalencias por categoría de fontanería, de mayor a menor cantidad."""
    cuentas: OrderedDict[str, list] = OrderedDict()
    for item in items:
        patron = match_plumbing(_texto(item))
        if patron is None:
            continue
        entrada = cuentas.setdefault(patron.category, [patron.what, patron.talend, 0])
        entrada[2] += 1
    filas = [Equivalencia(c, q, t, n) for c, (q, t, n) in cuentas.items()]
    return sorted(filas, key=lambda e: (-e.cantidad, e.categoria))


def seccion_equivalencias(equivalencias: list[Equivalencia]) -> dict[str, dict[str, str]]:
    """Sección 6: una fila por tipo de fontanería, con cuántas veces aparece."""
    return {
        f"{e.que} ({e.cantidad})": {"equivalente_talend": " ".join(e.talend.split())}
        for e in equivalencias
    }
