"""H3: similitud entre regiones por subsecuencia común más larga (LCS) de tipos de operador.

Variantes de la secuencia de cada región (todas parten del grafo tras la pasada 1):
- V0 `con_fontaneria`: todos los operadores. Es la medición previa (06-brecha-con-diseno.md).
- V1 `sin_fontaneria`: sin los marcados por la pasada 2 y sin los que una carga externa absorbe.
- V2 `sin_fontaneria_y_aristas`: V1 sin las lecturas de WORK que ya tienen productor (son aristas).
- V3 `v2_sin_repetidos`: V2 con los tipos consecutivos repetidos colapsados en uno.
- V4 `v2_sin_sin_traducir`: V2 sin los operadores `unsupported` (lo que el traductor no entiende).

Similitud estricta = LCS / max(largo a, largo b). Similitud de contención = LCS / min(...).
"""

from __future__ import annotations

import bisect
import statistics
from collections import defaultdict
from itertools import combinations

from fase0.captura import Captura, OpRec
from sgm.agrupacion import Declaracion, producto_por_region

MIN_GRANDE = 10  # pares donde ambas regiones tienen al menos este número de operadores


def lcs(a: list[str], b: list[str]) -> int:
    """Largo de la LCS con vectores de bits (Crochemore et al.); exacto, mucho más rápido que DP."""
    if not a or not b:
        return 0
    masks: dict[str, int] = defaultdict(int)
    for i, x in enumerate(a):
        masks[x] |= 1 << i
    todos = (1 << len(a)) - 1
    v = todos
    for y in b:
        m = masks.get(y, 0)
        u = v & m
        v = ((v + u) | (v & ~m)) & todos
    return len(a) - bin(v).count("1")


def lcs_dp(a: list[str], b: list[str]) -> int:
    """Referencia lenta para comprobar `lcs` en las pruebas internas del script."""
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def _es_arista(o: OpRec, producidos: set[str]) -> bool:
    d = (o.dataset or "").lower()
    return o.kind == "read" and d.startswith("work.") and d in producidos


def secuencias(c: Captura) -> dict[str, list[OpRec]]:
    """Operadores (en orden del programa) que quedan en cada variante, antes de pasar a tipos."""
    v0 = list(c.ops)
    v1 = [o for o in v0 if not o.plumbing and not o.absorbed and o.kind != "external_load"]
    ids_v1 = {o.id for o in v1}
    producidos: set[str] = set()
    v2: list[OpRec] = []
    for o in v0:  # los productores se acumulan en el orden del programa, con todos los operadores
        if o.id in ids_v1 and not _es_arista(o, producidos):
            v2.append(o)
        producidos |= {w.lower() for w in o.writes}
    return {
        "con_fontaneria": v0,
        "sin_fontaneria": v1,
        "sin_fontaneria_y_aristas": v2,
        "v2_sin_repetidos": v2,  # se colapsa al pasar a tipos
        "v2_sin_sin_traducir": [o for o in v2 if o.kind != "unsupported"],
    }


def _tipos(ops: list[OpRec], colapsar: bool) -> list[str]:
    tipos = [o.kind for o in ops]
    if colapsar:
        tipos = [t for i, t in enumerate(tipos) if i == 0 or t != tipos[i - 1]]
    return tipos


def _resumen(valores: list[float]) -> dict:
    if not valores:
        return {"n": 0}
    return {
        "n": len(valores),
        "min": round(min(valores), 3),
        "mediana": round(statistics.median(valores), 3),
        "media": round(statistics.mean(valores), 3),
        "max": round(max(valores), 3),
    }


def _region(o: OpRec, inicios: list[int], por: str) -> int:
    linea = o.region_line if por == "llamada" else o.line
    return bisect.bisect_right(inicios, linea) - 1 if linea else -1


def _variante(ops, inicios, colapsar, producto, por) -> dict:
    por_region: dict[int, list[OpRec]] = defaultdict(list)
    for o in ops:
        r = _region(o, inicios, por)
        if r >= 0:
            por_region[r].append(o)
    seq = {r: _tipos(v, colapsar) for r, v in por_region.items() if v}
    regiones = sorted(seq)
    estricta, contencion = {}, {}
    for a, b in combinations(regiones, 2):
        n = lcs(seq[a], seq[b])
        estricta[(a, b)] = n / max(len(seq[a]), len(seq[b]))
        contencion[(a, b)] = n / min(len(seq[a]), len(seq[b]))
    mayor = max(regiones, key=lambda r: len(seq[r])) if regiones else None
    frente_al_mayor = [
        estricta[tuple(sorted((r, mayor)))] for r in regiones if r != mayor and mayor is not None
    ]

    def partir(tabla):
        intra, inter = [], []
        for (a, b), s in tabla.items():
            if a in producto and b in producto:
                (intra if producto[a] == producto[b] else inter).append(s)
        return intra, inter

    grandes = [s for (a, b), s in estricta.items() if min(len(seq[a]), len(seq[b])) >= MIN_GRANDE]
    intra, inter = partir(estricta)
    intra_c, inter_c = partir(contencion)
    return {
        "regiones_con_operadores": len(regiones),
        "largo_por_region": {
            "min": min(map(len, seq.values())),
            "mediana": statistics.median(map(len, seq.values())),
            "max": max(map(len, seq.values())),
        }
        if seq
        else {},
        "region_mayor": mayor,
        "estricta_frente_a_la_region_mayor": _resumen(frente_al_mayor),
        "estricta_todos_los_pares": _resumen(list(estricta.values())),
        "contencion_todos_los_pares": _resumen(list(contencion.values())),
        f"estricta_pares_con_ambas_regiones_de_{MIN_GRANDE}_o_mas": _resumen(grandes),
        "estricta_intra_producto": _resumen(intra),
        "estricta_inter_producto": _resumen(inter),
        "contencion_intra_producto": _resumen(intra_c),
        "contencion_inter_producto": _resumen(inter_c),
    }


def _todas(c: Captura, inicios: list[int], producto: dict[int, str], por: str) -> dict:
    resultado = {}
    for nombre, ops in secuencias(c).items():
        resultado[nombre] = _variante(ops, inicios, nombre == "v2_sin_repetidos", producto, por)
        resultado[nombre]["operadores_en_regiones"] = sum(
            1 for o in ops if _region(o, inicios, por) >= 0
        )
    return resultado


def medir(c: Captura, inicios: list[int], decl: Declaracion | None) -> dict:
    """Dos asignaciones de operador a región: por la línea de la llamada de macro (principal) y por
    la línea del cuerpo donde está escrito (la que usa `sgm.generador`)."""
    producto = producto_por_region(c.hechos, inicios, decl) if decl else {}
    # Comprobación interna: la LCS rápida coincide con la de programación dinámica.
    muestra_a = ["read", "derive", "join", "write", "read", "filter"]
    muestra_b = ["derive", "read", "filter", "write", "join"]
    assert lcs(muestra_a, muestra_b) == lcs_dp(muestra_a, muestra_b)
    conteo: dict[str, int] = defaultdict(int)
    for p in producto.values():
        conteo[p] += 1
    return {
        "por_llamada_de_macro": _todas(c, inicios, producto, "llamada"),
        "por_cuerpo_de_macro": _todas(c, inicios, producto, "cuerpo"),
        "regiones_por_producto": dict(conteo),
        "regiones_sin_producto": len(inicios) - len(producto),
    }
