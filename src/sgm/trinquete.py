"""Trinquete de métricas (F1.0): un cambio que empeora una métrica no entra.

Las métricas de `06-calidad.md` que no estaban en `metrics.json` se calculan aquí:
- `tjava_sql`: componentes tJava cuyo origen es PROC SQL. Debe quedarse en 0.
- `excepciones`: programas que no compilaron (plan vacío con PARSE_ERROR del archivo).
- `huecos_por_motivo`: firmas de hueco por motivo.
- `lineas_sin_cubrir`: líneas con código que no aparecen en la evidencia de ningún operador, de
  `not_migrated` ni de un hueco. Un comentario o una línea en blanco no cuenta como código.

`check` compara con `metrics/baseline.json`. Ninguna métrica puede empeorar: subir cuando la buena
dirección es bajar, o bajar cuando es subir. El tiempo de compilación tiene 20 % de margen.
"""

from __future__ import annotations

from collections import Counter

from sgm import motivos
from sgm.compile import Compiled

TIME_MARGIN = 0.20
# Métricas de meta cero (fase 5.2): deben ser 0 siempre, no solo no empeorar.
METAS_CERO = ("pendientes_sin_dueno", "valores_sin_fuente")
# Dirección buena de cada métrica del total: "sube", "baja" o "mantiene" (no empeorar).
DIRECTIONS = {
    "pasos_por_componente": "sube",
    "pct_tjava": "baja",
    "tjava_sql": "baja",
    "subjobs": "baja",
    "lineas_sin_cubrir": "baja",
    "excepciones": "baja",
    "firmas_de_decision": "baja",
}


def code_lines(text: str) -> set[int]:
    """Números de línea (desde 1) con código: no vacías y fuera de comentarios /* */ y de `*`."""
    found: set[int] = set()
    in_comment = False
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if in_comment:
            if "*/" in stripped:
                in_comment = False
                stripped = stripped.split("*/", 1)[1].strip()
            else:
                continue
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_comment = True
                continue
            stripped = stripped.split("*/", 1)[1].strip()
        if not stripped or stripped.startswith("*"):
            continue
        found.add(number)
    return found


def _covered(plan) -> set[tuple[str, int]]:
    """(archivo, línea) cubiertos por algún operador, por `not_migrated` o por un hueco."""
    covered: set[tuple[str, int]] = set()

    def add(evidence) -> None:
        for ev in evidence:
            covered.update((ev.file, n) for n in range(ev.line_start, ev.line_end + 1))

    for op in plan.graph.operators():
        add(op.evidence)
    for nm in plan.not_migrated:
        add(nm.evidence)
    for gap in plan.gaps:
        add(gap.evidence)
    return covered


def uncovered_lines(compiled: dict[str, Compiled], files: dict[str, str]) -> int:
    """Líneas con código sin evidencia, sumadas sobre todos los programas."""
    total = 0
    for name, result in compiled.items():
        covered = _covered(result.plan)
        total += sum(1 for n in code_lines(files[name]) if (name, n) not in covered)
    return total


def extras(compiled: dict[str, Compiled], files: dict[str, str]) -> dict:
    """Métricas del trinquete para el total de `metrics.json`."""
    tjava_sql = 0
    failures = 0
    reasons: Counter[str] = Counter()
    decisions: set[str] = set()
    sin_dueno = 0
    sin_fuente = 0
    for result in compiled.values():
        for op in result.plan.graph.operators():
            if (
                op.component
                and op.component["name"] == "tJava"
                and (op.origin or "").startswith("proc_sql")
            ):
                tjava_sql += 1
        for op in result.plan.graph.operators():
            if op.component and op.component.get("name") not in (None, "none"):
                if not op.evidence:
                    sin_fuente += 1
        for gap in result.plan.gaps:
            if gap.signature.startswith("PARSE_ERROR:") and gap.reason == "PARSE_ERROR":
                failures += 1
            if motivos.de(gap.reason) is None:
                sin_dueno += 1
        reasons.update(gap.reason for gap in result.plan.gaps)
        decisions.update(p.signature for p in result.plan.pending)
    return {
        "tjava_sql": tjava_sql,
        "excepciones": failures,
        "huecos_por_motivo": dict(sorted(reasons.items())),
        "lineas_sin_cubrir": uncovered_lines(compiled, files),
        "firmas_de_decision": len(decisions),
        "pendientes_sin_dueno": sin_dueno,
        "valores_sin_fuente": sin_fuente,
    }


def check(current: dict, baseline: dict) -> list[str]:
    """Violaciones del trinquete: lista vacía si nada empeora frente a la línea base."""
    problems: list[str] = []
    now, was = current["total"], baseline["total"]
    if "programas" in was and now.get("programas") != was["programas"]:
        # Las cifras solo se comparan sobre el mismo corpus: si no, el trinquete no dice nada.
        problems.append(
            f"el corpus tiene {now.get('programas')} programas; "
            f"la línea base tiene {was['programas']}"
        )
        return problems
    for metric, direction in DIRECTIONS.items():
        if metric not in was:
            continue
        value, reference = now.get(metric, 0), was[metric]
        if direction == "sube" and value < reference:
            problems.append(f"{metric}: {value} < {reference} (debe subir)")
        if direction == "baja" and value > reference:
            problems.append(f"{metric}: {value} > {reference} (debe bajar)")
    for metric in METAS_CERO:
        if now.get(metric, 0) != 0:
            problems.append(f"{metric}: {now.get(metric)} (la meta es 0)")
    for reason, count in now.get("huecos_por_motivo", {}).items():
        reference = was.get("huecos_por_motivo", {}).get(reason, 0)
        if count > reference:
            problems.append(f"hueco {reason}: {count} > {reference}")
    seconds, reference_seconds = now.get("tiempo_compilacion_s"), was.get("tiempo_compilacion_s")
    if (
        seconds is not None
        and reference_seconds
        and seconds > reference_seconds * (1 + TIME_MARGIN)
    ):
        problems.append(
            f"tiempo_compilacion_s: {seconds} > {reference_seconds} + {TIME_MARGIN:.0%}"
        )
    return problems
