"""Etapas del programa: una tarjeta por sección, con una descripción en lenguaje llano.

Una etapa es una sección del programa (o un tramo de una sección muy grande). Su descripción sale
solo del tipo de cada paso y de los datasets que lee y escribe: si un paso no tiene un verbo
conocido, se dice su tipo tal cual, sin inventar qué hace.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

from sgm.flow.model import FlowModel, FlowStep
from sgm.flow.seccion import _agrupar
from sgm.flow.texto import es_dinamico

LIMITE_NOMBRES = 5  # datasets que se listan por etapa antes de resumir el resto

_VERBO_POR_TIPO = {
    "DATA step": "transforma datos",
    "PROC SQL": "consulta datos con SQL",
    "PROC SORT": "ordena datos",
    "PROC APPEND": "añade filas a una tabla",
    "PROC IMPORT": "importa un archivo",
    "PROC EXPORT": "exporta a un archivo",
    "PROC DELETE": "borra tablas",
    "PROC DATASETS": "gestiona tablas de una biblioteca",
    "PROC CONTENTS": "revisa la estructura de tablas",
    "PROC FORMAT": "define formatos",
    "PROC MEANS": "calcula resúmenes",
    "PROC SUMMARY": "calcula resúmenes",
    "PROC FREQ": "cuenta frecuencias",
    "Macro dinámica": "ejecuta bloques que dependen de macros",
}


@dataclass
class Etapa:
    """Una sección del programa, con lo que hace y con qué datasets trabaja."""

    titulo: str
    pasos: list[FlowStep]
    hace: str
    usa: list[str]
    produce: list[str]
    pendientes: int


def verbo_de(paso: FlowStep) -> str:
    """Frase corta de lo que hace un paso. Si el tipo no es conocido, se dice el tipo."""
    return _VERBO_POR_TIPO.get(paso.type_name, f"ejecuta {paso.type_name}")


def _unicos(valores: list[str]) -> list[str]:
    """Valores sin repetir, en orden de aparición."""
    vistos: list[str] = []
    for valor in valores:
        if valor not in vistos:
            vistos.append(valor)
    return vistos


def _frase_hace(pasos: list[FlowStep]) -> str:
    """Lista de verbos de la etapa, con la cuenta cuando se repiten: «transforma datos (×2)»."""
    verbos = [verbo_de(p) for p in pasos]
    partes = []
    for verbo in _unicos(verbos):
        veces = verbos.count(verbo)
        partes.append(verbo if veces == 1 else f"{verbo} ({veces} veces)")
    if not partes:
        return "No tiene pasos."
    texto = ", ".join(partes) + "."
    return texto[0].upper() + texto[1:]


def construir_etapas(model: FlowModel) -> list[Etapa]:
    """Etapas en el orden de aparición en el programa."""
    grupos, _, _ = _agrupar(model)
    pendientes_por_paso: dict[str, int] = {}
    for pendiente in model.pending:
        if pendiente.step_id:
            pendientes_por_paso[pendiente.step_id] = (
                pendientes_por_paso.get(pendiente.step_id, 0) + 1
            )
    etapas = []
    for titulo, pasos in grupos.items():
        lecturas = _unicos([n for p in pasos for n in p.reads])
        escrituras = _unicos([n for p in pasos for n in p.writes])
        etapas.append(
            Etapa(
                titulo=titulo,
                pasos=pasos,
                hace=_frase_hace(pasos),
                usa=lecturas,
                produce=escrituras,
                pendientes=sum(pendientes_por_paso.get(p.id, 0) for p in pasos),
            )
        )
    return etapas


def nombre_html(nombre: str) -> str:
    """Nombre de dataset en monoespaciado; si lleva macrovariable, se marca como dinámico."""
    badge = ""
    if es_dinamico(nombre):
        badge = (
            ' <span class="badge" title="Nombre con macrovariable sin resolver: depende de la '
            'ejecución">dinámico</span>'
        )
    return f'<span class="mono">{escape(nombre)}</span>{badge}'


def _lista_nombres(nombres: list[str]) -> str:
    """Hasta `LIMITE_NOMBRES` datasets y, si hay más, cuántos faltan."""
    if not nombres:
        return '<span class="nota">nada</span>'
    visibles = ", ".join(nombre_html(n) for n in nombres[:LIMITE_NOMBRES])
    resto = len(nombres) - LIMITE_NOMBRES
    if resto > 0:
        visibles += f' <span class="nota">y {resto} más</span>'
    return visibles


def _tarjeta(numero: int, etapa: Etapa) -> str:
    pasos = len(etapa.pasos)
    cuenta = f"{pasos} paso" if pasos == 1 else f"{pasos} pasos"
    lineas = [f"<p>{escape(etapa.hace)}</p>"]
    if etapa.usa:
        lineas.append(f'<p class="nota">Toma datos de: {_lista_nombres(etapa.usa)}</p>')
    if etapa.produce:
        lineas.append(f'<p class="nota">Deja datos en: {_lista_nombres(etapa.produce)}</p>')
    if etapa.pendientes:
        verbo = "depende" if etapa.pendientes == 1 else "dependen"
        partes = "parte" if etapa.pendientes == 1 else "partes"
        lineas.append(
            f'<p class="nota">{etapa.pendientes} {partes} de esta etapa {verbo} de valores que '
            "solo se conocen al ejecutar el programa.</p>"
        )
    return (
        f'<section class="etapa" id="etapa-{numero}"><div class="num">{numero}</div>'
        '<div class="cuerpo">'
        f'<h3>{escape(etapa.titulo)} <span class="nota">· {cuenta}</span></h3>'
        f"{''.join(lineas)}</div></section>"
    )


def render_etapas(model: FlowModel) -> str:
    """Tarjetas de etapas en orden. Sin pasos, un mensaje."""
    etapas = construir_etapas(model)
    if not etapas:
        return '<p class="nota">El programa no tiene etapas: no tiene pasos de datos.</p>'
    return "".join(_tarjeta(i, e) for i, e in enumerate(etapas, 1))
