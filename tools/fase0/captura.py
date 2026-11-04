"""Compila un programa con el frontend y la IR existentes y captura el estado intermedio.

La compilación real borra la fontanería del grafo (pasada 3), así que para medirla hay que mirar el
grafo justo antes de la pasada 2 y justo después de la pasada 3. Se envuelven esas dos funciones
mientras corre `compile_file` y se restauran al terminar; no se modifica `src/`.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from sgm.catalog.config import load_env
from sgm.compile import compile_file, project_base
from sgm.facts.model import Fact
from sgm.facts.project import facts_for_project
from sgm.frontend.program import analyze_program
from sgm.ir.builder import qualify
from sgm.ir.models import Operator
from sgm.passes import p02_plumbing, p03_intrinsics
from sgm.redaction import redact


@dataclass
class OpRec:
    """Un operador en el grafo justo después de la pasada 1 (antes de marcar fontanería)."""

    id: str
    kind: str
    line: int  # línea del cuerpo donde está escrito el operador
    region_line: int  # línea de la invocación más externa (si viene de una macro) o `line`
    reads: list[str]
    writes: list[str]
    dataset: str | None  # dataset de un `read`
    plumbing: str | None = None  # categoría de fontanería (pasada 2)
    absorbed: bool = False  # absorbido por una carga externa (pasada 3)
    removed: bool = False  # quitado como fontanería suelta (pasada 3)


@dataclass
class Captura:
    nombre: str
    texto: str
    lineas: list[str]
    items: int
    ops: list[OpRec]
    hechos: list[Fact]
    cargas_externas: int
    finales: Counter = field(default_factory=Counter)  # (tipo, estado) del plan final
    finales_total: int = 0
    sin_traducir: Counter = field(default_factory=Counter)  # operadores `unsupported` finales


def _linea_de_llamada(op: Operator) -> int | None:
    """Línea de la invocación de macro más externa (`línea:nombre`) si el operador sale de una
    expansión. Una macro definida una vez y llamada desde varias regiones deja la evidencia
    en el cuerpo, no en la región que la llama."""
    call = op.evidence[0].call if op.evidence else None
    if not call:
        return None
    m = re.search(r"(\d+):[^:]+$", call)
    return int(m.group(1)) if m else None


def _rec(op: Operator) -> OpRec:
    p = op.params
    reads: list[str] = []
    if op.kind == "read" and p.get("dataset"):
        reads.append(p["dataset"])
    for key in ("inputs", "sources"):
        reads += [n for n in p.get(key, []) if isinstance(n, str)]
    writes = [n for n in p.get("outputs", []) if isinstance(n, str)]
    if op.kind == "split" and p.get("target"):
        writes.append(qualify(p["target"]))
    line = op.evidence[0].line_start if op.evidence else 0
    region_line = _linea_de_llamada(op) or line
    ds = p.get("dataset") if op.kind == "read" else None
    return OpRec(op.id, op.kind, line, region_line, reads, writes, ds)


def _clave_sin_traducir(op: Operator) -> str:
    motivo = op.params.get("reason", "SIN_MOTIVO")
    return f"{op.origin or '-'} / {motivo}"


def capturar(ruta: Path) -> Captura:
    nombre = ruta.name
    texto = redact(ruta.read_text(encoding="utf-8", errors="replace"), nombre)
    base = project_base(env=load_env())
    externos = {k: redact(v, k) for k, v in base["external_files"].items()}
    analisis = analyze_program({nombre: texto}, externos)
    guardado: dict = {}
    mark_original, run_original = p02_plumbing.mark, p03_intrinsics.run

    def mark(graph, ctx):
        guardado["ops"] = [_rec(o) for o in sorted(graph.operators(), key=lambda o: o.id)]
        log = mark_original(graph, ctx)
        por_id = {o.id: o for o in graph.operators()}
        for rec in guardado["ops"]:
            rec.plumbing = por_id[rec.id].params.get("plumbing")
        return log

    def run(graph, ctx):
        log = run_original(graph, ctx)
        guardado["p03"] = log
        return log

    p02_plumbing.mark, p03_intrinsics.run = mark, run
    try:
        compilado = compile_file(analisis, nombre, base)
    finally:
        p02_plumbing.mark, p03_intrinsics.run = mark_original, run_original
    log3 = guardado["p03"]
    absorbidos = set(log3.merged)
    quitados = {r["op"] for r in log3.removed}
    for rec in guardado["ops"]:
        rec.absorbed = rec.id in absorbidos
        rec.removed = rec.id in quitados
    finales = list(compilado.plan.graph.operators())
    captura = Captura(
        nombre=nombre,
        texto=texto,
        lineas=texto.splitlines(),
        items=len(analisis.items),
        ops=guardado["ops"],
        hechos=facts_for_project({nombre: texto})[nombre],
        cargas_externas=int(log3.metrics.get("cargas_externas", 0)),
        finales=Counter((o.kind, o.status) for o in finales),
        finales_total=len(finales),
    )
    captura.sin_traducir = Counter(
        _clave_sin_traducir(o) for o in finales if o.kind == "unsupported"
    )
    return captura
