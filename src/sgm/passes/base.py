"""Protocolo de las pasadas y registro de lo que hace cada una.

Cada pasada es `run(graph, ctx) -> PassLog`. Solo transforma el grafo y registra lo que hizo:
operadores creados, fusionados, quitados (con motivo) y métricas. No guarda estado.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sgm.catalog.config import Project
from sgm.ir.models import Graph, Plan


@dataclass
class PassLog:
    name: str
    created: list[str] = field(default_factory=list)
    merged: list[str] = field(default_factory=list)
    removed: list[dict[str, str]] = field(default_factory=list)  # {"op", "motivo"}
    notes: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PassContext:
    """Lo que las pasadas necesitan además del grafo: el plan, los motores conocidos
    y las funciones SQL portables."""

    plan: Plan
    sql_portable: frozenset[str] = frozenset()
    library_engines: dict[str, str] = field(default_factory=dict)  # biblioteca -> motor
    schemas: dict[str, list] = field(default_factory=dict)  # esquemas de env/schemas.json
    project: Project = field(default_factory=Project)  # políticas de env/project.json


Pass = Callable[[Graph, PassContext], PassLog]
