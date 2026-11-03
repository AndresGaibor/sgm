"""Generador de joblets por grupo de regiones (sin pérdida, fase de diseño).

Pasos deterministas:
1. Regiones: cada definición de la macro que más veces se define en el programa (empates: la que
   aparece antes en el archivo). No se usa ningún nombre de cliente.
2. Grupos: `sgm.agrupacion` (vocabulario de conjuntos de datos, sin palabras comunes).
3. Joblet por grupo: unión de firmas de componente distintas de sus miembros, en orden de primera
   aparición. Cada miembro aporta un contexto con los conjuntos de datos que usa, en orden.

Lo que varía entre miembros (nombres y literales) queda en los contextos, no en el joblet.
"""

from __future__ import annotations

import bisect
import re
from collections import Counter, defaultdict

from sgm.agrupacion import agrupar, palabras_por_region
from sgm.facts.model import Fact

_DEF_MACRO = re.compile(r"^\s*%macro\s+([A-Za-z_]\w*)", re.I)


def marcador_de_regiones(lineas: list[str]) -> list[int]:
    """Líneas donde empieza cada región: definiciones de la macro más repetida del programa."""
    nombres = []
    for i, linea in enumerate(lineas):
        m = _DEF_MACRO.match(linea)
        if m:
            nombres.append((i + 1, m.group(1).lower()))
    conteo = Counter(n for _, n in nombres)
    if not conteo:
        return []
    repetida = max(conteo.values())
    if repetida < 2:
        return []
    ganador = next(n for _, n in nombres if conteo[n] == repetida)
    return [i for i, n in nombres if n == ganador]


def joblets_por_grupo(plan_ops, hechos: list[Fact], lineas: list[str]) -> list[dict]:
    """Un joblet por grupo de dos o más regiones, con sus contextos por miembro."""
    inicios = marcador_de_regiones(lineas)
    if len(inicios) < 2:
        return []
    palabras = palabras_por_region(hechos, inicios)
    grupos = [g for g in agrupar(palabras, 0.3).grupos if len(g) >= 2]
    por_region: dict[int, list] = defaultdict(list)
    for op in plan_ops:
        if op.evidence:
            por_region[bisect.bisect_right(inicios, op.evidence[0].line_start) - 1].append(op)
    datasets: dict[int, list[str]] = defaultdict(list)
    for h in hechos:
        if h.tipo not in ("tabla_escrita", "tabla_leida") or h.detalle.get("dinamico") == "si":
            continue
        r = bisect.bisect_right(inicios, h.linea_inicio) - 1
        if r >= 0 and h.valor not in datasets[r]:
            datasets[r].append(h.valor)
    salida = []
    for k, grupo in enumerate(grupos, 1):
        firmas: list[str] = []
        for r in grupo:
            for op in por_region.get(r, []):
                name = (op.component or {}).get("name")
                if name in (None, "none", "-", "tRunJob") or op.signature in firmas:
                    continue
                firmas.append(op.signature)
        contextos = [
            {f"tabla_{i + 1}": v for i, v in enumerate(datasets.get(r, []))} for r in grupo
        ]
        salida.append(
            {
                "id": f"jl_grupo_{k:02d}",
                "miembros": len(grupo),
                "firmas_de_componente": len(firmas),
                "contextos": contextos,
            }
        )
    return salida
