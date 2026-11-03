"""Agrupación determinista de regiones por proceso, sin reglas de nombres (fase 2 del diseño).

Método: cada región (delimitada por una definición de macro que se repite) se describe por las
palabras de los conjuntos de datos que escribe o lee. Las palabras que aparecen en más de la mitad
de las regiones son plomería y se descartan. Dos regiones se unen si la similitud de Jaccard de sus
palabras alcanza el umbral; los grupos son las componentes conexas.

No usa sufijos ni nombres de productos: cualquier programa con regiones repetidas se agrupa igual.
"""

from __future__ import annotations

import bisect
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from sgm.facts.model import Fact

_PALABRA = re.compile(r"[_.]")


@dataclass(frozen=True)
class Agrupacion:
    grupos: tuple[tuple[int, ...], ...]  # índices de región por grupo, de mayor a menor
    palabras: dict[int, frozenset[str]]


def _inicios(lineas: list[str], marcador: re.Pattern[str]) -> list[int]:
    return [i + 1 for i, linea in enumerate(lineas) if marcador.match(linea)]


def palabras_por_region(hechos: list[Fact], inicios: list[int]) -> dict[int, frozenset[str]]:
    """Palabras de los conjuntos de datos (escritos o leídos) de cada región."""
    palabras: dict[int, set[str]] = defaultdict(set)
    for h in hechos:
        if h.tipo not in ("tabla_escrita", "tabla_leida") or h.detalle.get("dinamico") == "si":
            continue
        r = bisect.bisect_right(inicios, h.linea_inicio) - 1
        if r < 0:
            continue
        for w in _PALABRA.split(h.valor.upper()):
            if len(w) >= 3 and w not in ("WORK", "TEMP"):
                palabras[r].add(w)
    return {r: frozenset(p) for r, p in palabras.items()}


def agrupar(
    palabras: dict[int, frozenset[str]], umbral: float = 0.3, df_maximo: float = 0.5
) -> Agrupacion:
    """Grupos de regiones por similitud de Jaccard entre sus palabras (sin plomería común)."""
    n = len(palabras)
    conteo = Counter(w for p in palabras.values() for w in p)
    comunes = {w for w, c in conteo.items() if n and c > n * df_maximo}
    limpias = {r: p - comunes for r, p in palabras.items()}
    padre = {r: r for r in limpias}

    def raiz(x: int) -> int:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    regiones = sorted(limpias)
    for i, a in enumerate(regiones):
        for b in regiones[i + 1 :]:
            union = limpias[a] | limpias[b]
            if union and len(limpias[a] & limpias[b]) / len(union) >= umbral:
                padre[raiz(a)] = raiz(b)
    grupos: dict[int, list[int]] = defaultdict(list)
    for r in regiones:
        grupos[raiz(r)].append(r)
    ordenados = sorted((tuple(g) for g in grupos.values()), key=lambda g: (-len(g), g))
    return Agrupacion(ordenados, limpias)


def inicios_de(lineas: list[str], marcador: str) -> list[int]:
    return _inicios(lineas, re.compile(marcador, re.I))
