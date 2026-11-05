"""Informe Markdown del corpus: casos por nivel con estado, capa, motivo y construcciones."""

from __future__ import annotations

from pathlib import Path

from .caso import Caso, todos_los_casos


def generar_informe(corpus: Path) -> str:
    """Devuelve el informe completo como texto Markdown."""
    casos = todos_los_casos(corpus)
    niveles = sorted({caso.nivel for caso in casos}, key=lambda n: int(n[1:]))
    lineas = ["# Informe del corpus", "", f"Casos en total: {len(casos)}.", ""]
    lineas += _resumen(casos, niveles)
    for nivel in niveles:
        grupo = [caso for caso in casos if caso.nivel == nivel]
        lineas += [f"## {nivel}", "", *_tabla_casos(grupo), ""]
        distintas = _construcciones(grupo)
        lineas += [f"Construcciones distintas en {nivel}: {', '.join(distintas) or 'ninguna'}.", ""]
    distintas = _construcciones(casos)
    lineas.append(f"Construcciones distintas en el corpus: {len(distintas)}.")
    return "\n".join(lineas) + "\n"


def _resumen(casos: list[Caso], niveles: list[str]) -> list[str]:
    lineas = [
        "| Nivel | Casos | Traducibles | Sin traducir | Construcciones distintas |",
        "|---|---:|---:|---:|---:|",
    ]
    for nivel in niveles:
        grupo = [caso for caso in casos if caso.nivel == nivel]
        traducibles = sum(1 for caso in grupo if caso.estado == "traducible")
        lineas.append(
            f"| {nivel} | {len(grupo)} | {traducibles} | {len(grupo) - traducibles} "
            f"| {len(_construcciones(grupo))} |"
        )
    return [*lineas, ""]


def _tabla_casos(grupo: list[Caso]) -> list[str]:
    lineas = [
        "| Caso | Estado | Capa | Motivo | Construcciones | N |",
        "|---|---|---|---|---|---:|",
    ]
    for caso in grupo:
        motivo = (caso.motivo or "").replace("|", "\\|")
        construcciones = ", ".join(caso.construcciones).replace("|", "\\|")
        lineas.append(
            f"| {caso.nombre} | {caso.estado} | {caso.capa} | {motivo} | {construcciones} "
            f"| {len(caso.construcciones)} |"
        )
    return lineas


def _construcciones(grupo: list[Caso]) -> list[str]:
    return sorted({construccion for caso in grupo for construccion in caso.construcciones})
