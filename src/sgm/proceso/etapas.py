"""Etapas de negocio declaradas: cada etiqueta `/* Etiqueta: ... */` se asigna a una etapa.

Las etapas y sus patrones son una decisión del equipo (`decisiones/<programa>.diseno.yaml`, clave
`etapas`): los patrones son palabras del negocio y no viven en el código. Gana la primera etapa de
la lista cuyo patrón casa con la etiqueta; una etiqueta sin etapa se lista, no se adivina.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class EtapaDeclarada:
    nombre: str
    patrones: tuple[re.Pattern[str], ...]


@dataclass
class Cobertura:
    """Cuántas etiquetas cayó en cada etapa y cuáles no tienen etapa."""

    por_etapa: Counter[str] = field(default_factory=Counter)
    sin_etapa: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(self.por_etapa.values()) + len(self.sin_etapa)

    @property
    def porcentaje_cubierto(self) -> float:
        return 100 * sum(self.por_etapa.values()) / self.total if self.total else 0.0


def cargar_etapas(path: Path) -> list[EtapaDeclarada]:
    """Lee la clave `etapas` del YAML. Un archivo mal formado falla con su nombre y el motivo."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    etapas: list[EtapaDeclarada] = []
    nombres: set[str] = set()
    for item in data.get("etapas") or []:
        item = item or {}
        nombre = str(item.get("nombre") or "").strip()
        textos = [str(p) for p in (item.get("patrones") or []) if str(p).strip()]
        if not nombre or not textos:
            raise ValueError(f"{path}: cada etapa necesita nombre y al menos un patrón")
        if nombre in nombres:
            raise ValueError(f"{path}: etapa repetida: {nombre}")
        nombres.add(nombre)
        try:
            patrones = tuple(re.compile(p, re.IGNORECASE) for p in textos)
        except re.error as error:
            raise ValueError(f"{path}: patrón inválido en la etapa {nombre}: {error}") from error
        etapas.append(EtapaDeclarada(nombre, patrones))
    if not etapas:
        raise ValueError(f"{path}: no hay etapas declaradas")
    return etapas


def etapa_de(etiqueta: str, etapas: list[EtapaDeclarada]) -> str | None:
    """Nombre de la primera etapa cuyo patrón casa con la etiqueta, o None."""
    for etapa in etapas:
        if any(p.search(etiqueta) for p in etapa.patrones):
            return etapa.nombre
    return None


def cobertura(etiquetas: list[str], etapas: list[EtapaDeclarada]) -> Cobertura:
    """Reparte las etiquetas entre las etapas declaradas."""
    res = Cobertura()
    for etiqueta in etiquetas:
        nombre = etapa_de(etiqueta, etapas)
        if nombre is None:
            res.sin_etapa.append(etiqueta)
        else:
            res.por_etapa[nombre] += 1
    return res
