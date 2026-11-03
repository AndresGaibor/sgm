"""Salidas del modelo de flujo que no son HTML: índice de datasets y JSON.

El índice de datasets responde "quién escribe X y quién lo lee", sin JavaScript.
El JSON deja el modelo completo para otras herramientas. Ninguna cambia el modelo.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from sgm.flow.model import FlowModel, dataset_key

VERSION_JSON = 1


@dataclass
class UsoDataset:
    """Un dataset con los pasos que lo escriben y los que lo leen, en orden de aparición."""

    nombre: str
    escriben: list[str] = field(default_factory=list)
    leen: list[str] = field(default_factory=list)


def indice_datasets(model: FlowModel) -> list[UsoDataset]:
    """Datasets del programa, ordenados por nombre, con sus pasos escritores y lectores."""
    usos: dict[str, UsoDataset] = {}
    for paso in model.steps:
        for nombre in paso.writes:
            uso = usos.setdefault(dataset_key(nombre), UsoDataset(nombre))
            if paso.id not in uso.escriben:
                uso.escriben.append(paso.id)
        for nombre in paso.reads:
            uso = usos.setdefault(dataset_key(nombre), UsoDataset(nombre))
            if paso.id not in uso.leen:
                uso.leen.append(paso.id)
    return sorted(usos.values(), key=lambda u: u.nombre.lower())


def a_json(model: FlowModel) -> str:
    """Modelo completo en JSON (pasos, conexiones, entradas, configuración y pendientes)."""
    datos = {
        "version": VERSION_JSON,
        "programa": model.program,
        "pasos": [asdict(p) for p in model.steps],
        "entradas": [asdict(p) for p in model.inputs],
        "conexiones": [asdict(e) for e in model.edges],
        "entradas_externas": model.external_inputs,
        "configuracion": [asdict(c) for c in model.config],
        "pendientes": [asdict(p) for p in model.pending],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"
