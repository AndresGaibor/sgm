"""Colapso por linaje (D1): cuántos bloques quedan si las tablas intermedias desaparecen.

Un paso de datos cuyo único resultado lo lee un solo paso siguiente se funde con él: la tabla entre
los dos es una arista, no una persistencia. La fontanería (reglas de `plumbing.yaml` y las
operaciones de transferencia) no cuenta. El resultado es una cota del tamaño del diseño, no el
número exacto de componentes: un bloque puede necesitar más de un componente.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from sgm.flow.model import FlowModel, FlowStep
from sgm.passes.plumbing_patterns import match_plumbing

# Pasos que mueven o borran datos sin transformarlos. Son tipos de SAS, no nombres del cliente.
TIPOS_SIN_DATOS = frozenset(
    {"PROC DELETE", "PROC UPLOAD", "PROC DOWNLOAD", "PROC PWENCODE", "PROC DATASETS"}
)


@dataclass
class Colapso:
    pasos_totales: int
    pasos_de_datos: int
    bloques: int
    bloques_por_region: dict[int, int] = field(default_factory=dict)
    pasos_por_region: dict[int, int] = field(default_factory=dict)
    bloques_por_region_etapa: dict[tuple[int, str], int] = field(default_factory=dict)


def es_fontaneria(paso: FlowStep) -> bool:
    """Paso sin datos: transferencia, borrado o texto que casa con una regla de fontanería."""
    if paso.type_name in TIPOS_SIN_DATOS:
        return True
    return match_plumbing(f"{paso.title}\n{paso.excerpt}") is not None


SIN_ETAPA = "(sin etapa)"


def colapsar(
    modelo: FlowModel,
    region_de_paso: dict[str, int],
    etapa_de_paso: Callable[[FlowStep], str | None] = lambda paso: None,
) -> Colapso:
    """Funde cadenas lineales de pasos de datos y cuenta los bloques por región y etapa."""
    datos = {p.id: p for p in modelo.steps if not es_fontaneria(p)}
    salientes: dict[str, list] = defaultdict(list)
    entrantes: dict[str, list] = defaultdict(list)
    for arista in modelo.edges:
        if arista.source in datos and arista.target in datos and arista.source != arista.target:
            salientes[arista.source].append(arista)
            entrantes[arista.target].append(arista)

    padre = {i: i for i in datos}

    def raiz(x: str) -> str:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for origen, aristas in salientes.items():
        if len(aristas) == 1 and len(entrantes[aristas[0].target]) == 1:
            padre[raiz(origen)] = raiz(aristas[0].target)

    bloques_region: dict[int, set[str]] = defaultdict(set)
    pasos_region: dict[int, int] = defaultdict(int)
    for id_paso in datos:
        region = region_de_paso.get(id_paso, 0)
        bloques_region[region].add(raiz(id_paso))
        pasos_region[region] += 1
    por_etapa: Counter[tuple[int, str]] = Counter()
    vistos: set[str] = set()
    for paso in modelo.steps:  # el bloque toma la etapa de su primer paso, en orden de programa
        if paso.id in datos and raiz(paso.id) not in vistos:
            vistos.add(raiz(paso.id))
            etapa = etapa_de_paso(paso) or SIN_ETAPA
            por_etapa[(region_de_paso.get(paso.id, 0), etapa)] += 1
    return Colapso(
        pasos_totales=len(modelo.steps),
        pasos_de_datos=len(datos),
        bloques=len({raiz(i) for i in datos}),
        bloques_por_region={r: len(b) for r, b in sorted(bloques_region.items())},
        pasos_por_region=dict(sorted(pasos_region.items())),
        bloques_por_region_etapa=dict(por_etapa),
    )


def bloques_de_plantillas(
    colapso: Colapso, familias: list[tuple[int, ...]], regiones_unicas: list[int]
) -> int:
    """Bloques si cada familia se escribe una vez (su región mayor) más las regiones sin copia."""
    total = sum(colapso.bloques_por_region.get(r, 0) for r in regiones_unicas)
    for miembros in familias:
        total += max(colapso.bloques_por_region.get(r, 0) for r in miembros)
    return total


def plantilla_por_etapa(
    colapso: Colapso,
    familias: list[tuple[int, ...]],
    regiones_unicas: list[int],
    eliminadas: frozenset[str] = frozenset(),
) -> dict[str, int]:
    """Bloques por etapa si cada familia se escribe una vez. Las etapas eliminadas no cuentan."""
    por_region: dict[int, Counter[str]] = defaultdict(Counter)
    for (region, etapa), n in colapso.bloques_por_region_etapa.items():
        por_region[region][etapa] += n
    elegidas = list(regiones_unicas)
    for miembros in familias:  # la región más grande representa a la familia
        elegidas.append(max(miembros, key=lambda r: sum(por_region[r].values())))
    total: Counter[str] = Counter()
    for region in elegidas:
        total.update({e: n for e, n in por_region[region].items() if e not in eliminadas})
    return dict(total.most_common())
