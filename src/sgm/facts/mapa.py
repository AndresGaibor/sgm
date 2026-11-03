"""Mapa de flujo en Markdown (fase 4.2): entiende un programa SAS sin traducirlo.

Sale solo de los hechos (`sgm.facts`): resumen, conjuntos de datos, entradas y salidas externas,
ramas de ambiente y lo que queda sin interpretar. No propone componentes ni Jobs.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from sgm.facts.model import Fact

NOTA = (
    "Este documento describe lo que el archivo dice. No demuestra que una traducción produzca "
    "los mismos datos; eso se verifica comparando salidas."
)


def _fuente(h: Fact) -> str:
    rango = (
        f"{h.linea_inicio}" if h.linea_inicio == h.linea_fin else f"{h.linea_inicio}-{h.linea_fin}"
    )
    return f"{h.archivo}:{rango}"


def _datasets(hechos: list[Fact]) -> list[str]:
    """Tabla de conjuntos de datos: escritos, leídos y borrados, por nombre."""
    filas: dict[str, dict] = defaultdict(
        lambda: {"alcance": "", "escrito": [], "leido": 0, "borrado": 0}
    )
    for h in hechos:
        if h.tipo not in ("tabla_escrita", "tabla_leida", "tabla_borrada"):
            continue
        if h.detalle.get("dinamico") == "si":
            continue  # nombre con macro variable: se reporta aparte
        fila = filas[h.valor.lower()]
        fila["alcance"] = fila["alcance"] or h.alcance
        if h.tipo == "tabla_escrita":
            fila["escrito"].append(h.linea_inicio)
        elif h.tipo == "tabla_leida":
            fila["leido"] += 1
        else:
            fila["borrado"] += 1
    lineas = [
        "| Conjunto | Alcance | Escrito en (líneas) | Leído (veces) | Borrado (veces) |",
        "|---|---|---|---|---|",
    ]
    for nombre in sorted(filas):
        f = filas[nombre]
        escrito = ", ".join(str(n) for n in sorted(set(f["escrito"]))[:5]) or "-"
        lineas.append(f"| {nombre} | {f['alcance']} | {escrito} | {f['leido']} | {f['borrado']} |")
    return lineas


def mapa_markdown(archivo: str, hechos: list[Fact]) -> str:
    """Documento Markdown del mapa de flujo de un programa."""
    conteo = Counter(h.tipo for h in hechos)
    dinamicos = [h for h in hechos if h.detalle.get("dinamico") == "si"]
    externas = [h for h in hechos if h.tipo in ("archivo_externo", "include_externo")]
    conexiones = sorted({h.valor for h in hechos if h.tipo == "conexion_base"})
    ramas = [h for h in hechos if h.tipo == "rama_por_valor"]
    desconocidos = [h for h in hechos if h.tipo == "desconocido"]
    partes = [
        f"# Mapa de flujo: {archivo}",
        "",
        f"> {NOTA}",
        "",
        "## Resumen",
        "",
        f"- Hechos: {len(hechos)}.",
        f"- Conjuntos de datos escritos: {conteo['tabla_escrita']}; "
        f"leídos: {conteo['tabla_leida']}; borrados: {conteo['tabla_borrada']}.",
        f"- Definiciones de macro: {conteo['macro_definida']}; "
        f"llamadas: {conteo['macro_llamada']}.",
        f"- Entradas o salidas externas: {len(externas)}; conexiones a base: {len(conexiones)}.",
        f"- Ramas por valor de ambiente: {len(ramas)}.",
        f"- Sin interpretar: {len(desconocidos)}; nombres dinámicos: {len(dinamicos)}.",
        "",
        "## Conjuntos de datos",
        "",
        *_datasets(hechos),
        "",
        "## Entradas y salidas externas",
        "",
    ]
    if externas:
        partes += ["| Tipo | Valor | Fuente |", "|---|---|---|"]
        partes += [f"| {h.tipo} | {h.valor} | {_fuente(h)} |" for h in externas]
    else:
        partes.append("No hay entradas ni salidas externas declaradas.")
    partes += ["", "## Conexiones a base", ""]
    partes += [f"- {c}" for c in conexiones] or ["No hay conexiones a base."]
    partes += ["", "## Ramas por valor de ambiente", ""]
    if ramas:
        partes += [
            f"- `{h.valor}` ({_fuente(h)}): valores {h.detalle.get('valores', '')}" for h in ramas
        ]
    else:
        partes.append("No hay ramas por valor.")
    partes += ["", "## Pendientes", ""]
    if desconocidos:
        partes += [
            f"- {h.detalle.get('reason', 'sin motivo')} en {_fuente(h)}" for h in desconocidos[:50]
        ]
        if len(desconocidos) > 50:
            partes.append(f"- ... y {len(desconocidos) - 50} más en el JSON.")
    else:
        partes.append("Ningún fragmento queda sin interpretar.")
    return "\n".join(partes) + "\n"
