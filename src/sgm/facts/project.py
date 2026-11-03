"""Hechos de un proyecto: analiza como `compile` y devuelve los hechos de cada archivo.

Usa la misma redacción y las mismas externas que la compilación, así que un hecho nunca ve una
credencial en claro y los hechos y el plan hablan del mismo texto.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from sgm.compile import project_base
from sgm.facts.model import Fact
from sgm.facts.structural import structural_facts
from sgm.facts.textual import libref_externos, textual_facts
from sgm.frontend.lexer import split_statements
from sgm.frontend.macros import MacroDynamic
from sgm.frontend.program import ProgramAnalysis, analyze_program
from sgm.frontend.splitter import split_nodes
from sgm.frontend.steps import MacroDef, parse_steps
from sgm.redaction import redact


def _ordena(raws: list[dict]) -> list[dict]:
    return sorted(
        raws,
        key=lambda r: (r["inicio"], r["fin"], r["tipo"], r["valor"], r.get("extractor", "")),
    )


# Palabras del lenguaje de macros que no son llamadas a macros de usuario.
_MACRO_SENTENCIAS = {
    "let", "if", "then", "else", "do", "end", "to", "by", "while", "until", "put", "global",
    "local", "macro", "mend", "include", "return", "goto", "label", "window", "display",
    "symdel", "copy", "abort", "run",
}  # fmt: skip
# Funciones del lenguaje de macros: son `funcion_usada`, no llamadas de usuario.
_MACRO_FUNCIONES = {
    "sysfunc", "qsysfunc", "scan", "qscan", "substr", "qsubstr", "upcase", "qupcase", "lowcase",
    "trim", "eval", "sysevalf", "str", "nrstr", "quote", "nrquote", "unquote", "length", "index",
    "left", "right", "cmpres", "superq", "bquote", "nrbquote", "sysget", "symexist", "countw",
    "qtrim", "qleft", "qright", "sysmacexec", "symget", "sysexec",
}  # fmt: skip
_MACRO_CALL = re.compile(r"%([A-Za-z_]\w*)(?=\s*[(;])")


def _llamadas_del_texto(texto: str) -> list[dict]:
    """Llamadas a macros y funciones del lenguaje de macros, leídas del texto del archivo.

    Se leen del texto y no de la expansión: una llamada cuyo cuerpo se expande a nada no deja
    ningún paso, y aun así está en el archivo.
    """
    raws = []
    for m in _MACRO_CALL.finditer(texto):
        nombre = m.group(1).lower()
        if nombre in _MACRO_SENTENCIAS or nombre == "macro":
            continue
        if nombre not in _MACRO_FUNCIONES:
            continue  # las llamadas a macros de usuario salen de los pasos (MacroCall)
        linea = texto.count("\n", 0, m.start()) + 1
        raws.append(
            {
                "tipo": "funcion_usada",
                "valor": m.group(1),
                "alcance": "no_aplica",
                "inicio": linea,
                "fin": linea,
                "detalle": {},
                "extractor": "textual",
                "nodo": None,
            }
        )
    return raws


def _todos_los_pasos(pasos: list[object]) -> Iterator[object]:
    """Pasos del texto, incluido el cuerpo de cada definición de macro (aunque no se invoque)."""
    for paso in pasos:
        yield paso
        if isinstance(paso, MacroDef):
            yield from _todos_los_pasos(paso.body)


def _etiqueta(nodos: list, linea: int) -> str | None:
    found = None
    for nodo in nodos:
        if nodo.line_start > linea:
            break
        found = nodo.label
    return found


def _facts_for_file(
    file: str, analysis: ProgramAnalysis, libref: set[str], texto: str
) -> list[Fact]:
    raws: list[dict] = _llamadas_del_texto(texto)
    # Los pasos salen del texto, no del análisis: el análisis expande las macros invocadas y
    # descarta las copias idénticas; leer el texto cubre cada copia con sus propias líneas.
    nodos = split_nodes(texto)
    pasos, _ = parse_steps(split_statements(texto))
    for paso in _todos_los_pasos(pasos):
        etiqueta = _etiqueta(nodos, int(getattr(paso, "line", 1) or 1))
        for raw in structural_facts(paso, libref):
            raws.append({**raw, "extractor": "estructural", "nodo": etiqueta})
        for raw in textual_facts(paso, libref):
            raws.append({**raw, "extractor": "textual", "nodo": etiqueta})
    # Los fragmentos que dependen de la ejecución solo existen en el análisis.
    for pi in analysis.items:
        if pi.file == file and isinstance(pi.item, MacroDynamic):
            for raw in textual_facts(pi.item, libref):
                raws.append({**raw, "extractor": "textual", "nodo": pi.label})
    for use in analysis.selector_uses:
        if use.file != file:
            continue
        sel = use.selector
        raws.append(
            {
                "tipo": "rama_por_valor",
                "valor": sel.variable,
                "alcance": "no_aplica",
                "inicio": use.line,
                "fin": use.line,
                "detalle": {"valores": ",".join(sel.variables), "macro": sel.name},
                "extractor": "selector",
                "nodo": None,
            }
        )
    facts: list[Fact] = []
    seen: set[tuple] = set()
    for raw in _ordena(raws):
        key = (raw["tipo"], raw["valor"], raw["inicio"], raw["fin"], raw["extractor"])
        if key in seen:
            continue
        seen.add(key)
        detalle = dict(raw.get("detalle", {}))
        if "&" in str(raw["valor"]) or "%" in str(raw["valor"]):
            detalle["dinamico"] = "si"  # el nombre depende de una macro variable
        facts.append(
            Fact(
                id=f"h-{len(facts) + 1:06d}",
                tipo=raw["tipo"],
                valor=str(raw["valor"]),
                alcance=raw["alcance"],
                archivo=file,
                linea_inicio=int(raw["inicio"]),
                linea_fin=int(raw["fin"]),
                extractor=raw["extractor"],
                nodo=raw.get("nodo"),
                detalle=detalle,
            )
        )
    return facts


def facts_for_project(files: dict[str, str]) -> dict[str, list[Fact]]:
    """Hechos de cada archivo. `files` es {ruta relativa: texto}."""
    clean = {path: redact(text, path) for path, text in files.items()}
    base = project_base()
    externals = {path: redact(text, path) for path, text in base["external_files"].items()}
    analysis = analyze_program(clean, externals)
    all_items = [pi.item for pi in analysis.items]
    libref = libref_externos(all_items)
    return {file: _facts_for_file(file, analysis, libref, clean[file]) for file in sorted(clean)}
