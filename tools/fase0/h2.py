"""H2: ciclo de vida de los conjuntos de datos que el programa escribe (hechos de texto).

Una "versión" es una escritura de un nombre; sus lectores son las lecturas que vienen después, hasta
la siguiente escritura del mismo nombre. Una región es el tramo desde un marcador de región hasta el
siguiente (-1 es el encabezado, antes del primero). Los nombres con macro variables (`&x`) no se
pueden resolver sin ejecutar y se cuentan aparte.
"""

from __future__ import annotations

import bisect
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from sgm.agrupacion import Declaracion
from sgm.facts.model import Fact


@dataclass
class Version:
    nombre: str
    alcance: str
    region: int
    linea: int
    importada: bool
    lecturas: list[tuple[int, bool]] = field(default_factory=list)  # (región, es exportación)


def _norm(valor: str) -> str:
    n = valor.strip().lower()
    return n[5:] if n.startswith("work.") else n


def _sin_producto(nombre: str, sufijos: set[str]) -> str:
    for s in sorted(sufijos, key=len, reverse=True):
        if nombre.endswith("_" + s):
            return nombre[: -len(s) - 1]
    return nombre


def _colapsar(nombres, sufijos: set[str]) -> set[str]:
    return {_sin_producto(n, sufijos) for n in nombres}


def _clase(v: Version) -> str:
    if v.importada:
        return "fuente_importada"
    if not v.lecturas:
        return "sin_lector"
    if any(exp for _, exp in v.lecturas):
        return "exportada"
    if all(r == v.region for r, _ in v.lecturas):
        return "local_a_region"
    return "cruza_region"


def versiones(hechos: list[Fact], inicios: list[int]):
    """(versiones, lecturas sin productor previo, cantidad de nombres dinámicos descartados)."""
    imports = {h.linea_inicio for h in hechos if h.detalle.get("procedimiento") == "import"}
    exports = {h.linea_inicio for h in hechos if h.detalle.get("procedimiento") == "export"}
    eventos = []
    dinamicos = 0
    for i, h in enumerate(hechos):
        if h.tipo not in ("tabla_leida", "tabla_escrita"):
            continue
        if h.detalle.get("dinamico") == "si" or "&" in h.valor:
            dinamicos += 1
            continue
        if _norm(h.valor) == "_null_":  # `data _null_` no crea ningún dataset
            continue
        eventos.append((h.linea_inicio, 1 if h.tipo == "tabla_escrita" else 0, i, h))
    eventos.sort(key=lambda e: e[:3])  # en una misma línea, primero las lecturas
    actual: dict[str, Version] = {}
    cerradas: list[Version] = []
    huerfanas: dict[str, tuple[str, set[int]]] = {}  # nombre -> (alcance, regiones)
    for linea, es_escritura, _i, h in eventos:
        nombre = _norm(h.valor)
        region = bisect.bisect_right(inicios, linea) - 1
        if es_escritura:
            if nombre in actual:
                cerradas.append(actual[nombre])
            actual[nombre] = Version(nombre, h.alcance, region, linea, linea in imports)
        elif nombre in actual:
            actual[nombre].lecturas.append((region, linea in exports))
        else:
            huerfanas.setdefault(nombre, (h.alcance, set()))[1].add(region)
    return cerradas + list(actual.values()), huerfanas, dinamicos


def _por_nombre(vs: list[Version]) -> dict[str, list[Version]]:
    grupos: dict[str, list[Version]] = defaultdict(list)
    for v in vs:
        grupos[v.nombre].append(v)
    return grupos


# Idiomas de SAS genéricos: un WORK pasado como literal a `%scan` es lo que un macro de carga masiva
# toma como origen, y un `WITH x AS (` define una tabla temporal de la consulta, no una tabla.
_CARGA_LITERAL = re.compile(r"(?i)%scan\(\s*work\.(\w+)")
_CTE = re.compile(r"(?i)(?:\bwith|,)\s+(\w+)\s+as\s*\(")


def filas_de_tabla(ruta: Path | None, titulo: str) -> int | None:
    """Filas de la primera tabla bajo un encabezado cuyo texto contiene `titulo` (sin cabecera)."""
    if ruta is None or not ruta.exists():
        return None
    dentro, n = False, 0
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("#"):
            if dentro:
                break
            dentro = titulo.lower() in linea.lower()
        elif dentro and re.match(r"^\|", linea):
            n += 1
    return max(n - 2, 0) if n else None  # cabecera y separador


def medir(hechos, inicios, decl: Declaracion | None, diseno: Path | None, texto: str) -> dict:
    vs, huerfanas, dinamicos = versiones(hechos, inicios)
    sufijos = {s.lower() for ss in (decl.productos.values() if decl else ()) for s in ss}
    work = [v for v in vs if v.alcance == "work"]
    base = [v for v in vs if v.alcance != "work"]
    clases = Counter(_clase(v) for v in work)
    nombres_work = _por_nombre(work)
    una_vez = {n: g[0] for n, g in nombres_work.items() if len(g) == 1}
    una_vez_local = [n for n, v in una_vez.items() if _clase(v) == "local_a_region"]
    una_vez_cruza = [n for n, v in una_vez.items() if _clase(v) == "cruza_region"]
    reescritos = {n: len(g) for n, g in nombres_work.items() if len(g) > 1}
    local_versiones = [v for v in work if _clase(v) == "local_a_region"]
    exportadas = {v.nombre for v in work if _clase(v) == "exportada"}
    n_exportaciones = sum(1 for h in hechos if h.detalle.get("procedimiento") == "export")
    work_sin_lector = {v.nombre for v in work if _clase(v) == "sin_lector"}
    base_sin_lector = {v.nombre for v in base if not v.lecturas}
    base_con_lector = {v.nombre for v in base if v.lecturas}
    importados = {h.valor for h in hechos if h.detalle.get("procedimiento") == "import"}
    descargas = {h.valor for h in hechos if h.detalle.get("procedimiento") == "download"}
    cargados = {n.lower() for n in _CARGA_LITERAL.findall(texto)}
    ctes = {n.lower() for n in _CTE.findall(texto)}
    todas_base = sorted(n for n, (a, _) in huerfanas.items() if a != "work" and n not in ctes)
    descartadas_cte = sorted(n for n, (a, _) in huerfanas.items() if a != "work" and n in ctes)
    nombre_corto = lambda n: n.split(".", 1)[-1]  # noqa: E731
    recargas = [n for n in todas_base if nombre_corto(n) in cargados]
    fuentes_base = [n for n in todas_base if nombre_corto(n) not in cargados]
    leidas_de_base = {nombre_corto(n) for n in todas_base}
    cargados_y_releidos = cargados & leidas_de_base
    fuentes_work = sorted(n for n, (a, _) in huerfanas.items() if a == "work")
    work_sin_lector_real = work_sin_lector - cargados
    salidas = exportadas | base_sin_lector | (cargados - cargados_y_releidos)
    return {
        "nombres_dinamicos_descartados": dinamicos,
        "work": {
            "escrituras_o_versiones": len(work),
            "nombres_distintos": len(nombres_work),
            "versiones_por_clase": dict(clases.most_common()),
            "nombres_escritos_una_sola_vez": len(una_vez),
            "una_vez_y_local_a_su_region": len(una_vez_local),
            "una_vez_y_cruza_region": len(una_vez_cruza),
            "nombres_reescritos_mas_de_una_vez": len(reescritos),
            "reescritos_top": dict(sorted(reescritos.items(), key=lambda kv: -kv[1])[:5]),
            "versiones_locales_a_region": len(local_versiones),
        },
        "permanentes_o_de_base": {
            "versiones": len(base),
            "nombres_distintos": len({v.nombre for v in base}),
            "sin_lector_en_el_programa": len(base_sin_lector),
            "con_lector_en_el_programa": len(base_con_lector),
        },
        "fuentes_externas": {
            "archivos_importados_distintos": len(importados),
            "archivos_descargados_distintos": len(descargas),
            "tablas_de_base_leidas_sin_escribirlas_antes_externas": len(fuentes_base),
            "tablas_de_base_que_son_recarga_de_un_work_propio": len(recargas),
            "nombres_de_cte_descartados": descartadas_cte,
            "tablas_de_base_colapsando_sufijo_de_producto": len(_colapsar(fuentes_base, sufijos)),
            "work_leidas_sin_productor_previo": fuentes_work,
            "total_fuentes_distintas": len(importados) + len(fuentes_base),
            "total_colapsando_sufijo": len(importados) + len(_colapsar(fuentes_base, sufijos)),
            "archivos_importados": sorted(importados),
            "tablas_de_base": fuentes_base,
            "recargas_de_un_work_propio": recargas,
        },
        "salidas_finales": {
            "sentencias_de_exportacion": n_exportaciones,
            "datasets_exportados_distintos": len(exportadas),
            "tablas_de_base_sin_lector": len(base_sin_lector),
            "work_cargados_a_base_por_macro": len(cargados),
            "de_los_cuales_se_releen_desde_la_base": len(cargados_y_releidos),
            "de_los_cuales_no_se_releen": len(cargados - cargados_y_releidos),
            "work_sin_lector_ni_exportacion_ni_carga": len(work_sin_lector_real),
            "total_salidas_distintas": len(salidas),
            "total_colapsando_sufijo": len(_colapsar(salidas, sufijos)),
        },
        "diseno_manual": {
            "fuentes_externas": filas_de_tabla(diseno, "Fuentes externas"),
            "salidas": filas_de_tabla(diseno, "Salidas"),
        },
    }
