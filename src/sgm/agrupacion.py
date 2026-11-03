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
from pathlib import Path

import yaml

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
    # Con pocas regiones todo el vocabulario sería "común": el filtro solo aplica desde seis.
    comunes = {w for w, c in conteo.items() if n >= 6 and c > n * df_maximo}
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


@dataclass(frozen=True)
class Declaracion:
    """Agrupación decidida por el equipo: un producto por sufijo de sus conjuntos de datos.

    Vive en `decisiones/<programa>.agrupacion.yaml` y la revisa una persona. No es un hecho del SAS:
    el archivo no demuestra qué regiones son el mismo proceso.
    """

    marcador: str
    productos: dict[str, tuple[str, ...]]  # nombre -> sufijos en mayúsculas


def cargar_declaracion(path: Path) -> Declaracion:
    """Lee la agrupación declarada. Un archivo mal formado falla con su nombre y el motivo."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    marcador = str(data.get("region_marcador") or "").strip()
    if not marcador:
        raise ValueError(f"{path}: falta region_marcador")
    productos: dict[str, tuple[str, ...]] = {}
    for item in data.get("productos") or []:
        item = item or {}
        nombre = str(item.get("nombre") or "").strip()
        sufijos = tuple(
            str(s).strip().upper() for s in (item.get("sufijos") or []) if str(s).strip()
        )
        if not nombre or not sufijos:
            raise ValueError(f"{path}: cada producto necesita nombre y al menos un sufijo")
        productos[nombre] = sufijos
    if not productos:
        raise ValueError(f"{path}: no hay productos declarados")
    return Declaracion(marcador=marcador, productos=productos)


def producto_por_region(
    hechos: list[Fact], inicios: list[int], declaracion: Declaracion
) -> dict[int, str]:
    """Producto dominante de cada región: el de más conjuntos de datos con su sufijo.

    Empate: gana el producto declarado primero. Una región sin coincidencias no tiene producto y
    queda como pendiente, no se adivina.
    """
    orden = list(declaracion.productos)
    cuenta: dict[int, Counter[str]] = defaultdict(Counter)
    for h in hechos:
        if h.tipo not in ("tabla_escrita", "tabla_leida") or h.detalle.get("dinamico") == "si":
            continue
        r = bisect.bisect_right(inicios, h.linea_inicio) - 1
        if r < 0:
            continue
        nombre = h.valor.upper()
        for producto, sufijos in declaracion.productos.items():
            if any(nombre.endswith("_" + s) for s in sufijos):
                cuenta[r][producto] += 1
    return {
        r: max(c.most_common(), key=lambda kv: (kv[1], -orden.index(kv[0])))[0]
        for r, c in cuenta.items()
        if c
    }


def grupos_declarados(
    hechos: list[Fact], inicios: list[int], declaracion: Declaracion
) -> tuple[tuple[int, ...], ...]:
    """Regiones agrupadas por producto declarado, de mayor a menor. Las sueltas quedan fuera."""
    grupos: dict[str, list[int]] = defaultdict(list)
    for r, producto in sorted(producto_por_region(hechos, inicios, declaracion).items()):
        grupos[producto].append(r)
    ordenados = [tuple(g) for g in grupos.values() if len(g) >= 2]
    return tuple(sorted(ordenados, key=lambda g: (-len(g), g)))
