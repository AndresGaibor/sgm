"""Diagnóstico de agrupación: de dónde salen los componentes y los `tJava` (`out/diagnostico.md`).

Responde a tres preguntas sin cambiar el comportamiento de la compilación:
1. ¿Qué constructo SAS de origen produce cada componente y cada `tJava`?
2. ¿Qué hace cada pasada: operadores creados, fusionados y quitados?
3. ¿Por qué se corta un subjob, y cuántas decisiones son firmas distintas?
"""

from __future__ import annotations

from collections import Counter, defaultdict

from sgm.compile import Compiled

SIN_ORIGEN = "creado_por_pasada"  # operadores que crean las pasadas (fusiones, plantillas, cargas)


def _origin_table(compiled: dict[str, Compiled]) -> tuple[Counter, Counter, Counter]:
    """Componentes por origen, tJava por origen y componentes por (origen, nombre)."""
    by_origin: Counter[str] = Counter()
    java_by_origin: Counter[str] = Counter()
    by_pair: Counter[tuple[str, str]] = Counter()
    for result in compiled.values():
        for op in result.plan.graph.operators():
            if not op.component or op.component["name"] == "none":
                continue
            origin = op.origin or SIN_ORIGEN
            name = op.component["name"]
            by_origin[origin] += 1
            by_pair[(origin, name)] += 1
            if name == "tJava":
                java_by_origin[origin] += 1
    return by_origin, java_by_origin, by_pair


def _pass_table(compiled: dict[str, Compiled]) -> dict[str, dict[str, int]]:
    """Por pasada: operadores creados, fusionados y quitados, sumados sobre todos los programas."""
    empty = {"creados": 0, "fusionados": 0, "quitados": 0}
    table: dict[str, dict[str, int]] = defaultdict(lambda: dict(empty))
    for result in compiled.values():
        for log in result.logs:
            row = table[log.name]
            row["creados"] += len(log.created)
            row["fusionados"] += len(log.merged)
            row["quitados"] += len(log.removed)
    return dict(table)


def _decision_table(compiled: dict[str, Compiled]) -> list[tuple[str, int, int]]:
    """Firma de decisión, veces que aparece y archivos distintos, de mayor a menor."""
    counts: Counter[str] = Counter()
    files: dict[str, set[str]] = defaultdict(set)
    for result in compiled.values():
        for pending in result.plan.pending:
            counts[pending.signature] += 1
            files[pending.signature].add(result.plan.program)
    return [(sig, n, len(files[sig])) for sig, n in counts.most_common()]


def _pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f} %" if whole else "0 %"


def build(compiled: dict[str, Compiled]) -> dict:
    by_origin, java_by_origin, by_pair = _origin_table(compiled)
    total = sum(by_origin.values())
    java = sum(java_by_origin.values())
    return {
        "componentes": total,
        "tjava": java,
        "por_origen": by_origin,
        "tjava_por_origen": java_by_origin,
        "por_origen_y_nombre": by_pair,
        "pasadas": _pass_table(compiled),
        "decisiones": _decision_table(compiled),
    }


def render(data: dict, report: dict) -> str:
    """Markdown del diagnóstico. `report` es el resultado de `sgm.metrics.compute`."""
    total = report["total"]
    lines = [
        "# Diagnóstico de agrupación",
        "",
        "Generado por `sgm metrics`. Solo describe; no cambia la compilación.",
        "",
        "## Totales",
        "",
        f"- Pasos SAS: {total['pasos_sas']}; nodos SAS: {total['nodos_sas']}",
        f"- Componentes: {data['componentes']}",
        f"- Pasos SAS por componente: {total['pasos_por_componente']}",
        f"- Nodos SAS por componente: {total['nodos_por_componente']}",
        f"- tJava: {data['tjava']} ({_pct(data['tjava'], data['componentes'])})",
        f"- Subjobs: {total['subjobs']}",
        f"- Decisiones: {total['decisiones_pendientes']} totales, "
        f"{total['firmas_de_decision']} firmas únicas",
        "",
        "## Componentes por constructo de origen",
        "",
        "| origen | componentes | % | tJava | componentes por nombre |",
        "|---|---|---|---|---|",
    ]
    names = _names_by_origin(data["por_origen_y_nombre"])
    for origin, count in data["por_origen"].most_common():
        lines.append(
            f"| {origin} | {count} | {_pct(count, data['componentes'])} "
            f"| {data['tjava_por_origen'].get(origin, 0)} | {names[origin]} |"
        )
    lines += [
        "",
        "## Operadores por pasada",
        "",
        "| pasada | creados | fusionados | quitados |",
        "|---|---|---|---|",
    ]
    for name, row in data["pasadas"].items():
        lines.append(f"| {name} | {row['creados']} | {row['fusionados']} | {row['quitados']} |")
    lines += ["", "## Subjobs por motivo de corte", "", "| motivo | cortes |", "|---|---|"]
    cuts: Counter[str] = Counter()
    for program in report["programas"].values():
        cuts.update(program["cortes_de_subjob"])
    lines += [f"| {reason} | {count} |" for reason, count in cuts.most_common()]
    lines += [
        "",
        "## Decisiones por firma (las 20 primeras)",
        "",
        "| firma | veces | archivos |",
        "|---|---|---|",
    ]
    lines += [f"| `{sig}` | {n} | {files} |" for sig, n, files in data["decisiones"][:20]]
    return "\n".join(lines) + "\n"


def _names_by_origin(by_pair: Counter) -> dict[str, str]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for (origin, name), count in by_pair.items():
        grouped[origin][name] += count
    return {
        origin: ", ".join(f"{name} {n}" for name, n in pairs.most_common())
        for origin, pairs in grouped.items()
    }
