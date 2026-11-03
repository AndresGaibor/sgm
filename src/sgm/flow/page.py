"""Página HTML del flujo de un programa: resumen, diagrama, pasos en orden y pendientes.

Es un archivo estático con CSS y SVG, sin scripts ni recursos externos. Todo texto que viene del
programa SAS se escapa antes de escribirse.
"""

from __future__ import annotations

from datetime import date
from html import escape

from sgm.flow.layout import render_svg
from sgm.flow.model import DIAGRAMA_POR_PASO_MAX, FlowModel, FlowStep, Pending
from sgm.flow.salida import indice_datasets
from sgm.flow.seccion import by_section

_CSS = """
:root {
  --fondo: #f6f7f9; --panel: #ffffff; --texto: #1d2430; --suave: #5b6676; --linea: #d9dee6;
  --data: #2563eb; --sql: #059669; --proc: #d97706; --externo: #64748b;
  --dinamico: #dc2626; --sin-leer: #e11d48;
  --data-f: #e8efff; --sql-f: #e6f7f1; --proc-f: #fdf1e0; --externo-f: #eef1f5;
  --dinamico-f: #fde8e8; --sin-leer-f: #ffe8ef;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --fondo: #0f1419; --panel: #171d24; --texto: #e6e9ef; --suave: #9aa5b5; --linea: #2a3340;
    --data-f: #1c2a4a; --sql-f: #15332a; --proc-f: #3a2c14; --externo-f: #222a35;
    --dinamico-f: #3d1b1b; --sin-leer-f: #3d1b26;
  }
}
:root[data-theme="dark"] {
  --fondo: #0f1419; --panel: #171d24; --texto: #e6e9ef; --suave: #9aa5b5; --linea: #2a3340;
  --data-f: #1c2a4a; --sql-f: #15332a; --proc-f: #3a2c14; --externo-f: #222a35;
  --dinamico-f: #3d1b1b; --sin-leer-f: #3d1b26;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--fondo); color: var(--texto);
  font: 15px/1.5 system-ui, "Segoe UI", Roboto, sans-serif; }
main { max-width: 1280px; margin: 0 auto; padding: 28px 24px 64px; }
h1 { font-size: 26px; margin: 0 0 4px; }
h2 { font-size: 19px; margin: 40px 0 12px; }
.resumen { color: var(--suave); margin: 0 0 20px; }
.tarjetas { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
.tarjeta { background: var(--panel); border: 1px solid var(--linea); border-radius: 12px;
  padding: 14px 16px; }
.tarjeta b { display: block; font-size: 26px; }
.tarjeta span { color: var(--suave); font-size: 13px; }
.leyenda { display: flex; flex-wrap: wrap; gap: 14px; margin: 14px 0; font-size: 13px; }
.leyenda i { display: inline-block; width: 12px; height: 12px; border-radius: 3px;
  margin-right: 6px; vertical-align: -1px; }
.marco { background: var(--panel); border: 1px solid var(--linea); border-radius: 12px;
  padding: 16px; overflow: auto; }
.nodo rect { stroke-width: 1.5; }
.nodo .tipo { font-size: 11px; text-transform: uppercase; letter-spacing: .04em;
  fill: var(--suave); }
.nodo .titulo { font-size: 14px; font-weight: 600; fill: var(--texto); }
.nodo .sub { font-size: 11.5px; fill: var(--suave); }
.k-data rect { fill: var(--data-f); stroke: var(--data); }
.k-sql rect { fill: var(--sql-f); stroke: var(--sql); }
.k-proc rect { fill: var(--proc-f); stroke: var(--proc); }
.k-external rect { fill: var(--externo-f); stroke: var(--externo); stroke-dasharray: 5 4; }
.k-dynamic rect { fill: var(--dinamico-f); stroke: var(--dinamico); }
.k-unparsed rect { fill: var(--sin-leer-f); stroke: var(--sin-leer); stroke-dasharray: 2 3; }
.k-section rect { fill: var(--panel); stroke: var(--texto); stroke-width: 2; }
.arista path { fill: none; stroke: var(--suave); stroke-width: 1.6; opacity: .8; }
.arista text { font-size: 11px; fill: var(--texto); paint-order: stroke; stroke: var(--panel);
  stroke-width: 4px; }
#flecha path { fill: var(--suave); }
table { width: 100%; border-collapse: collapse; background: var(--panel); font-size: 14px;
  border: 1px solid var(--linea); border-radius: 12px; overflow: hidden; }
th, td { text-align: left; padding: 9px 11px; border-bottom: 1px solid var(--linea);
  vertical-align: top; }
th { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--suave); }
td code, .mono { font: 12.5px/1.45 ui-monospace, Consolas, monospace; }
pre { background: var(--fondo); border: 1px solid var(--linea); border-radius: 8px;
  padding: 10px 12px; overflow: auto; font: 12.5px/1.45 ui-monospace, Consolas, monospace;
  white-space: pre; margin: 8px 0 0; }
details summary { cursor: pointer; color: var(--suave); font-size: 13px; }
.etiqueta { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px;
  background: var(--fondo); border: 1px solid var(--linea); color: var(--suave); }
ul.lista { padding-left: 20px; margin: 0; }
.nota { color: var(--suave); font-size: 13px; }
footer { color: var(--suave); font-size: 12px; margin-top: 40px; }
"""

_LEYENDA = [
    ("k-data", "DATA step"),
    ("k-sql", "PROC SQL"),
    ("k-proc", "Otro PROC"),
    ("k-external", "Entrada externa"),
    ("k-dynamic", "Macro dinámica"),
    ("k-unparsed", "Sin leer"),
]
_COLOR_LEYENDA = {
    "k-data": "var(--data)",
    "k-sql": "var(--sql)",
    "k-proc": "var(--proc)",
    "k-external": "var(--externo)",
    "k-dynamic": "var(--dinamico)",
    "k-unparsed": "var(--sin-leer)",
    "k-section": "var(--texto)",
}


def _macro_name(call: str | None) -> str | None:
    """Nombre de la macro a partir de `archivo:línea:nombre`."""
    return call.rsplit(":", 1)[-1] if call else None


def _summary(model: FlowModel) -> str:
    conexiones = len(model.edges)
    pendientes = len(model.pending)
    cards = [
        (len(model.steps), "pasos del programa"),
        (len(model.external_inputs), "entradas externas"),
        (conexiones, "conexiones entre datasets"),
        (pendientes, "pendientes"),
    ]
    html = "".join(
        f'<div class="tarjeta"><b>{n}</b><span>{escape(label)}</span></div>' for n, label in cards
    )
    return f'<section class="tarjetas">{html}</section>'


def _legend(por_seccion: bool) -> str:
    entradas = [*_LEYENDA, ("k-section", "Sección")] if por_seccion else _LEYENDA
    items = "".join(
        f'<span><i style="background:{_COLOR_LEYENDA[cls]}"></i>{escape(label)}</span>'
        for cls, label in entradas
    )
    return f'<div class="leyenda">{items}</div>'


def _step_row(step: FlowStep) -> str:
    anchor = f"paso-{step.id}"
    macro = _macro_name(step.macro_call)
    origen = f"{step.file}:{step.line}"
    notas = list(step.notes)
    if macro:
        notas.insert(0, f"generado por la macro %{macro}")
    notas_html = "<br>".join(escape(n) for n in notas) or '<span class="nota">-</span>'
    reads = ", ".join(step.reads) or "-"
    writes = ", ".join(step.writes) or "-"
    return (
        f'<tr id="{anchor}"><td>{escape(step.id)}</td>'
        f'<td class="mono">{escape(origen)}</td>'
        f"<td>{escape(step.type_name)}</td>"
        f"<td>{escape(step.title)}</td>"
        f'<td class="mono">{escape(reads)}</td>'
        f'<td class="mono">{escape(writes)}</td>'
        f"<td>{notas_html}"
        f"<details><summary>ver código</summary><pre>{escape(step.excerpt)}</pre></details>"
        "</td></tr>"
    )


def _steps_table(model: FlowModel) -> str:
    if not model.steps:
        return '<p class="nota">El programa no tiene pasos de datos.</p>'
    rows = "".join(_step_row(step) for step in model.steps)
    return (
        "<table><thead><tr><th>#</th><th>Origen</th><th>Tipo</th><th>Qué hace</th>"
        "<th>Lee</th><th>Escribe</th><th>Notas y código</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _config_table(model: FlowModel) -> str:
    if not model.config:
        return '<p class="nota">Sin sentencias de configuración.</p>'
    rows = "".join(
        f'<tr><td class="mono">{escape(c.kind)}</td><td class="mono">{c.line}</td>'
        f'<td class="mono">{escape(c.text)}</td></tr>'
        for c in model.config
    )
    return (
        "<table><thead><tr><th>Tipo</th><th>Línea</th><th>Sentencia</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _inputs_list(model: FlowModel) -> str:
    if not model.inputs:
        return '<p class="nota">Ningún dataset se lee sin haberlo escrito antes en el programa.</p>'
    items = "".join(
        f'<li id="entrada-{node.id}"><span class="mono">{escape(node.title)}</span>'
        f' <span class="nota">se usa en {len([e for e in model.edges if e.source == node.id])}'
        " paso(s)</span></li>"
        for node in model.inputs
    )
    return f'<ul class="lista">{items}</ul>'


def _pending_item(pendiente: Pending) -> str:
    texto = escape(pendiente.text)
    if pendiente.step_id:
        return f'<li><a href="#paso-{pendiente.step_id}">{texto}</a></li>'
    return f"<li>{texto}</li>"


def _pending_list(model: FlowModel) -> str:
    if not model.pending:
        return '<p class="nota">Sin pendientes en este programa.</p>'
    items = "".join(_pending_item(p) for p in model.pending)
    return f'<ul class="lista">{items}</ul>'


def _links(ids: list[str], titulos: dict[str, str]) -> str:
    """Enlaces a las filas de la tabla de pasos, con el título del paso como ayuda."""
    if not ids:
        return '<span class="nota">-</span>'
    return ", ".join(
        f'<a href="#paso-{i}" title="{escape(titulos.get(i, ""))}">{i}</a>' for i in ids
    )


def _datasets_table(model: FlowModel) -> str:
    """Un dataset por fila: qué pasos lo escriben y cuáles lo leen. Sin JavaScript."""
    usos = indice_datasets(model)
    if not usos:
        return '<p class="nota">El programa no lee ni escribe datasets en sus pasos.</p>'
    titulos = {s.id: s.title for s in model.steps}
    filas = "".join(
        f'<tr><td class="mono">{escape(u.nombre)}</td>'
        f"<td>{_links(u.escriben, titulos)}</td>"
        f"<td>{_links(u.leen, titulos)}</td></tr>"
        for u in usos
    )
    return (
        "<table><thead><tr><th>Dataset</th><th>Lo escriben</th><th>Lo leen</th></tr></thead>"
        f"<tbody>{filas}</tbody></table>"
    )


def render_page(model: FlowModel) -> str:
    """Documento HTML completo del flujo de un programa."""
    titulo = f"Flujo SAS: {model.program}"
    por_seccion = len(model.steps) > DIAGRAMA_POR_PASO_MAX
    diagrama = by_section(model) if por_seccion else model
    if por_seccion:
        nota_diagrama = (
            f"El programa tiene {len(model.steps)} pasos, demasiados para dibujarlos uno a uno. "
            "El diagrama muestra una caja por sección del programa, con el número de pasos "
            "de cada una. Cada caja enlaza con la tabla de pasos, donde está el detalle."
        )
    else:
        nota_diagrama = (
            "Cada caja es un paso del programa. Pasa el cursor para ver lo que lee y escribe."
        )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<style>{_CSS}</style>
</head>
<body>
<main>
<h1>{escape(model.program)}</h1>
<p class="resumen">Cómo funciona el programa: pasos en orden y los datasets que pasan de uno a
otro. No es la traducción a Talend. Cada caja enlaza con su fila de la tabla.</p>
{_summary(model)}
<h2>Diagrama</h2>
<p class="nota">{escape(nota_diagrama)}</p>
{_legend(por_seccion)}
<div class="marco">{render_svg(diagrama)}</div>
<h2 id="pasos">Pasos en orden</h2>
{_steps_table(model)}
<h2>Datasets</h2>
<p class="nota">Cada dataset y los pasos que lo escriben o lo leen. Cada número enlaza con su
fila en la tabla de pasos.</p>
{_datasets_table(model)}
<h2>Entradas externas</h2>
<p class="nota">Datasets que el programa lee y que ningún paso anterior escribe. Vienen de fuera
del programa.</p>
{_inputs_list(model)}
<h2>Configuración</h2>
<p class="nota">Librerías, variables, opciones, includes y macros que definen el entorno.</p>
{_config_table(model)}
<h2>Pendientes</h2>
{_pending_list(model)}
<footer>Generado el {date.today().isoformat()} por `sgm flujo`. Vista de revisión: no cambia el
plan ni la guía.</footer>
</main>
</body>
</html>
"""
