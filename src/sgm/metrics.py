"""Métricas de compilación: por programa y total, en `out/metrics.json`.

- Nodos SAS por componente Talend: nodos con etiqueta dividido entre componentes candidatos. Más
alto es mejor:
  significa que cada componente agrupa más código SAS.
- Jobs y subjobs por programa.
- Operadores por estado.
- Componentes por peldaño de la escalera, y el porcentaje de tJava.
- Pasos sin pendientes: componentes que no necesitan revisión.
- Decisiones pendientes.
- Las 10 firmas de huecos con más ocurrencias.
"""

from __future__ import annotations

from collections import Counter

from sgm.compile import Compiled
from sgm.frontend.splitter import split_nodes
from sgm.store import gaps as gap_store


def _program_metrics(compiled: Compiled, nodes: int) -> dict:
    plan = compiled.plan
    operators = plan.graph.operators()
    components = [
        op.component for op in operators if op.component and op.component["name"] != "none"
    ]
    rungs = Counter(c["rung"] for c in components)
    java = sum(1 for c in components if c["name"] == "tJava")
    return {
        "nodos_sas": nodes,
        "componentes": len(components),
        "nodos_por_componente": round(nodes / len(components), 3) if components else 0.0,
        "componentes_por_nombre": dict(Counter(c["name"] for c in components).most_common()),
        "jobs": len(plan.jobs),
        "subjobs": sum(len(j.subjobs) for j in plan.jobs),
        "operadores": len(operators),
        "operadores_por_estado": dict(Counter(op.status for op in operators)),
        "componentes_por_peldano": {str(k): v for k, v in sorted(rungs.items())},
        "pct_tjava": round(100 * java / len(components), 1) if components else 0.0,
        "pasos_sin_pendientes": sum(1 for c in components if not c.get("needs_review")),
        "decisiones_pendientes": len(plan.pending),
        "huecos": len(plan.gaps),
    }


def compute(compiled: dict[str, Compiled], files: dict[str, str]) -> dict:
    """Métricas por programa y del total. `files` da el número de nodos SAS de cada programa."""
    programs: dict[str, dict] = {}
    for name, result in compiled.items():
        nodes = len([n for n in split_nodes(files[name]) if n.label is not None])
        programs[name] = _program_metrics(result, nodes)
    total = {
        "programas": len(programs),
        "nodos_sas": sum(p["nodos_sas"] for p in programs.values()),
        "componentes": sum(p["componentes"] for p in programs.values()),
        "jobs": sum(p["jobs"] for p in programs.values()),
        "subjobs": sum(p["subjobs"] for p in programs.values()),
        "pasos_sin_pendientes": sum(p["pasos_sin_pendientes"] for p in programs.values()),
        "decisiones_pendientes": sum(p["decisiones_pendientes"] for p in programs.values()),
    }
    componentes = total["componentes"]
    total["nodos_por_componente"] = (
        round(total["nodos_sas"] / componentes, 3) if componentes else 0.0
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
