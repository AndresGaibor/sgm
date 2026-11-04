"""Familias de regiones: copias de un mismo proceso que solo cambian el producto.

Método: se normaliza cada región (sin comentarios, en minúsculas, con el sufijo de producto
sustituido por `{P}`) y se compara línea a línea. Dos regiones con parecido igual o mayor al umbral
son de la misma familia; la familia tiene una plantilla y una instancia por producto. Lo que difiere
fuera del sufijo (`diferencias`) es justo lo que hay que parametrizar o revisar.

Los sufijos llegan como parámetro desde el YAML de decisiones: no hay nombres de producto aquí.
El parecido por líneas es una medida de texto, no demuestra equivalencia semántica.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import combinations

MARCADOR_PRODUCTO = "{P}"
UMBRAL_FAMILIA = 0.85

_COMENTARIO = re.compile(r"/\*.*?\*/", re.DOTALL)


@dataclass(frozen=True)
class Instancia:
    """Una región de la familia y el producto que se le dedujo (None si no se pudo decidir)."""

    region: int
    producto: str | None


@dataclass(frozen=True)
class Familia:
    id: int
    instancias: tuple[Instancia, ...]  # por índice de región
    similitud_minima: float  # el peor par de la familia
    lineas: int  # mediana de líneas normalizadas de sus regiones

    @property
    def productos_repetidos(self) -> tuple[str, ...]:
        """Productos con más de una región en la familia (copias que el producto no distingue)."""
        cuenta = Counter(i.producto for i in self.instancias if i.producto)
        return tuple(sorted(p for p, n in cuenta.items() if n > 1))


@dataclass(frozen=True)
class ResultadoFamilias:
    familias: tuple[Familia, ...]
    unicas: tuple[int, ...]  # regiones sin copia


def patron_sufijos(sufijos: list[str]) -> re.Pattern[str] | None:
    if not sufijos:
        return None
    alternativas = "|".join(re.escape(s) for s in sorted(sufijos, key=len, reverse=True))
    return re.compile(rf"(?<=_)(?:{alternativas})(?![A-Za-z0-9])", re.IGNORECASE)


def normalizar_region(texto: str, sufijos: list[str]) -> list[str]:
    """Líneas de la región sin comentarios de bloque, en minúsculas y con el sufijo sustituido."""
    patron = patron_sufijos(sufijos)
    sin_comentarios = _COMENTARIO.sub(" ", texto)
    lineas: list[str] = []
    for cruda in sin_comentarios.split("\n"):
        linea = " ".join(cruda.split()).lower()
        if not linea:
            continue
        if patron:
            linea = patron.sub(MARCADOR_PRODUCTO, linea)
        lineas.append(linea)
    return lineas


def producto_de_texto(texto: str, productos: dict[str, tuple[str, ...]]) -> str | None:
    """Producto con más apariciones de su sufijo en el texto; el empate o la ausencia dan None."""
    cuenta: Counter[str] = Counter()
    for nombre, sufijos in productos.items():
        patron = patron_sufijos(list(sufijos))
        if patron:
            cuenta[nombre] = len(patron.findall(texto))
    if not cuenta:
        return None
    ordenados = cuenta.most_common()
    if ordenados[0][1] == 0:
        return None
    if len(ordenados) > 1 and ordenados[1][1] == ordenados[0][1]:
        return None
    return ordenados[0][0]


def similitud(a: list[str], b: list[str], minimo: float = 0.0) -> float:
    """Parecido por líneas entre 0 y 1. Si por tamaño y contenido no puede llegar a `minimo`, 0."""
    if not a or not b:
        return 0.0
    comunes = sum((Counter(a) & Counter(b)).values())
    if 2 * comunes / (len(a) + len(b)) < minimo:
        return 0.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def diferencias(a: list[str], b: list[str]) -> list[tuple[list[str], list[str]]]:
    """Tramos que cambian entre dos regiones normalizadas: (líneas de a, líneas de b)."""
    cambios = SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    return [(a[i1:i2], b[j1:j2]) for tag, i1, i2, j1, j2 in cambios if tag != "equal"]


def _mediana(valores: list[int]) -> int:
    ordenados = sorted(valores)
    return ordenados[len(ordenados) // 2]


def detectar_familias(
    lineas: dict[int, list[str]],
    productos: dict[int, str | None],
    umbral: float = UMBRAL_FAMILIA,
) -> ResultadoFamilias:
    """Agrupa las regiones por parecido normalizado. Las que no tienen copia quedan en `unicas`."""
    indices = sorted(lineas)
    padre = {r: r for r in indices}

    def raiz(x: int) -> int:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    pares: dict[tuple[int, int], float] = {}
    for a, b in combinations(indices, 2):
        valor = similitud(lineas[a], lineas[b], umbral)
        if valor >= umbral:
            pares[(a, b)] = valor
            padre[raiz(a)] = raiz(b)

    miembros: dict[int, list[int]] = {}
    for r in indices:
        miembros.setdefault(raiz(r), []).append(r)

    familias: list[Familia] = []
    unicas: list[int] = []
    for grupo in sorted(miembros.values()):
        if len(grupo) < 2:
            unicas.extend(grupo)
            continue
        peor = min(
            pares.get((a, b)) or similitud(lineas[a], lineas[b]) for a, b in combinations(grupo, 2)
        )
        familias.append(
            Familia(
                id=len(familias) + 1,
                instancias=tuple(Instancia(r, productos.get(r)) for r in grupo),
                similitud_minima=round(peor, 3),
                lineas=_mediana([len(lineas[r]) for r in grupo]),
            )
        )
    return ResultadoFamilias(tuple(familias), tuple(sorted(unicas)))
