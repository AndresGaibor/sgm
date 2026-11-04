"""Página HTML que explica en lenguaje llano qué hace un programa SAS, sin mostrar su código.

Va de lo general a lo particular: una frase, qué datos entran y salen, las etapas en orden y los
puntos que no se pueden seguir sin ejecutar el programa. Es un archivo estático con CSS en línea,
sin scripts ni recursos externos. Todo texto que viene del programa SAS se escapa antes de
escribirse.

"""

from __future__ import annotations

from datetime import date
from html import escape

from sgm.flow.estilo import CSS
from sgm.flow.etapas import nombre_html, render_etapas
from sgm.flow.model import FlowModel
from sgm.flow.salida import UsoDataset, salidas_finales
from sgm.flow.texto import frase_resumen


def _inputs_list(model: FlowModel) -> str:
    if not model.inputs:
        return (
            '<p class="nota">Ningún dato entra desde fuera: el programa crea todo lo que usa.</p>'
        )
    items = "".join(f"<li>{nombre_html(node.title)}</li>" for node in model.inputs)
    return f'<ul class="lista">{items}</ul>'


def _outputs_list(salidas: list[UsoDataset]) -> str:
    if not salidas:
        return '<p class="nota">El programa no deja ningún resultado que nadie use después.</p>'
    items = "".join(f"<li>{nombre_html(u.nombre)}</li>" for u in salidas)
    return f'<ul class="lista">{items}</ul>'


def _pendientes(model: FlowModel) -> str:
    """Puntos que el análisis no puede seguir. Se dicen en palabras, sin referencias de línea."""
    if not model.pending:
        return '<p class="nota">No hay nada que el análisis no pueda seguir.</p>'
    items = "".join(f"<li>{escape(p.text)}</li>" for p in model.pending)
    return (
        '<p class="nota">Estas partes dependen de valores que solo se conocen al ejecutar el '
        "programa. Para entenderlas hay que correrlo o revisarlas a mano.</p>"
        f'<ul class="lista">{items}</ul>'
    )


def _bloque(titulo: str, nota: str, contenido: str) -> str:
    return f'<div class="bloque"><h3>{titulo}</h3><p class="nota">{nota}</p>{contenido}</div>'


def render_page(model: FlowModel) -> str:
    """Documento HTML que explica el programa: frase, entradas y salidas, etapas y pendientes."""
    titulo = f"Qué hace {model.program}"
    salidas = salidas_finales(model)
    frase = frase_resumen(model, [u.nombre for u in salidas])
    entran = _bloque(
        "Qué datos entran",
        "Datos que el programa toma de fuera y que no crea antes.",
        _inputs_list(model),
    )
    salen = _bloque(
        "Qué resultados quedan",
        "Datos que el programa produce y que nadie usa después.",
        _outputs_list(salidas),
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>{escape(model.program)}</h1>
<p class="resumen">Explicación del programa en lenguaje llano. No muestra el código.</p>
<p class="frase">{escape(frase)}</p>
<div class="dos">{entran}{salen}</div>
<h2>Cómo funciona, paso a paso</h2>
<p class="nota">Cada etapa es una parte del programa. Se ejecutan en el orden de esta lista.
Cada una dice qué hace y qué datos toma y deja.</p>
{render_etapas(model)}
<h2>Lo que no se puede seguir sin ejecutarlo</h2>
{_pendientes(model)}
<footer>Generado el {date.today().isoformat()} por `sgm flujo`. Vista de revisión: no cambia el
plan ni la guía.</footer>
</main>
</body>
</html>
"""
