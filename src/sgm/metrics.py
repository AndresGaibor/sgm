"""Métricas de compilación: por programa y total, en `out/metrics.json`.

- Pasos SAS por componente Talend (métrica principal, ronda 2): pasos del programa expandido
  (`ProgramItem`; un nodo de SAS Studio puede tener varios) dividido entre componentes candidatos.
  Más alto es mejor: cada componente agrupa más trabajo SAS.
- Nodos SAS por componente (se conserva de la ronda 1).
- Jobs y subjobs por programa; subjobs por motivo de corte.
- Operadores por estado; componentes por peldaño de la escalera; porcentaje de tJava.
- Pasos sin pendientes; decisiones pendientes, totales y firmas únicas.
- Las 10 firmas de huecos con más ocurrencias.
El desglose por origen SAS va en `out/diagnostico.md` (ver `sgm.diagnostics`).
"""

from __future__ import annotations

from collections import Counter

from sgm.compile import Compiled
from sgm.frontend.program import ProgramAnalysis
from sgm.frontend.splitter import split_nodes
from sgm.store import gaps as gap_store


def components_of(compiled: Compiled) -> list[dict]:
    """Componentes candidatos de un plan (sin los `none`, que no son componentes)."""
    return [
        op.component
        for op in compiled.plan.graph.operators()
        if op.component and op.component["name"] != "none"
    ]


def _program_metrics(compiled: Compiled, nodes: int, steps: int) -> dict:
    plan = compiled.plan
    operators = plan.graph.operators()
    components = components_of(compiled)
    rungs = Counter(c["rung"] for c in components)
    java = sum(1 for c in components if c["name"] == "tJava")
    cuts: Counter[str] = Counter()
    for log in compiled.logs:
        cuts.update(log.metrics.get("cortes", {}))
    return {
        "nodos_sas": nodes,
        "pasos_sas": steps,
        "componentes": len(components),
        "nodos_por_componente": round(nodes / len(components), 3) if components else 0.0,
        "pasos_por_componente": round(steps / len(components), 3) if components else 0.0,
        "componentes_por_nombre": dict(Counter(c["name"] for c in components).most_common()),
        "jobs": len(plan.jobs),
        "subjobs": sum(len(j.subjobs) for j in plan.jobs),
        "cortes_de_subjob": dict(sorted(cuts.items())),
        "operadores": len(operators),
        "operadores_por_estado": dict(Counter(op.status for op in operators)),
        "componentes_por_peldano": {str(k): v for k, v in sorted(rungs.items())},
        "pct_tjava": round(100 * java / len(components), 1) if components else 0.0,
        "pasos_sin_pendientes": sum(1 for c in components if not c.get("needs_review")),
        "decisiones_pendientes": len(plan.pending),
        "firmas_de_decision": len({p.signature for p in plan.pending}),
        "huecos": len(plan.gaps),
    }


def compute(
    compiled: dict[str, Compiled], files: dict[str, str], analysis: ProgramAnalysis
) -> dict:
    """Métricas por programa y del total. `files` da los nodos; `analysis`, los pasos."""
    steps = Counter(item.file for item in analysis.items)
    programs: dict[str, dict] = {}
    for name, result in compiled.items():
        nodes = len([n for n in split_nodes(files[name]) if n.label is not None])
        programs[name] = _program_metrics(result, nodes, steps[name])
    total = {
        "programas": len(programs),
        "nodos_sas": sum(p["nodos_sas"] for p in programs.values()),
        "pasos_sas": sum(p["pasos_sas"] for p in programs.values()),
        "componentes": sum(p["componentes"] for p in programs.values()),
        "jobs": sum(p["jobs"] for p in programs.values()),
        "subjobs": sum(p["subjobs"] for p in programs.values()),
        "pasos_sin_pendientes": sum(p["pasos_sin_pendientes"] for p in programs.values()),
        "decisiones_pendientes": sum(p["decisiones_pendientes"] for p in programs.values()),
        "firmas_de_decision": len({p.signature for r in compiled.values() for p in r.plan.pending}),
    }
    componentes = total["componentes"]
    total["nodos_por_componente"] = (
        round(total["nodos_sas"] / componentes, 3) if componentes else 0.0
    )
    total["pasos_por_componente"] = (
        round(total["pasos_sas"] / componentes, 3) if componentes else 0.0
    )
    java = sum(p["componentes_por_nombre"].get("tJava", 0) for p in programs.values())
    total["pct_tjava"] = round(100 * java / componentes, 1) if componentes else 0.0
    return {"total": total, "programas": programs, "top_huecos": top_gaps(compiled)}


def top_gaps(compiled: dict[str, Compiled], n: int = 10) -> list[dict]:
    rows = gap_store.inventory([c.plan for c in compiled.values()])
    rows.sort(key=lambda r: (-r["occurrences"], r["signature"]))
    return [
        {
            "signature": r["signature"],
            "reason": r["reason"],
            "occurrences": r["occurrences"],
            "files": len(r["files"]),
            "texto": (r["example"] or {}).get("texto", ""),
        }
        for r in rows[:n]
    ]
