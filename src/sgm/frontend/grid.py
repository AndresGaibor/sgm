"""Modelo de ejecución (SAS Grid): qué se lanza, en qué orden, con qué parámetros.

Separado del modelo de procesamiento de datos: una espera entre trabajos es una dependencia de
orquestación, nunca una conexión de filas entre componentes. Las dependencias se marcan
`inferred` cuando salen de la secuencia del script y no de una declaración explícita.

Porte parcial: se conservan el análisis de los scripts de shell (`sasgsub`, `sas -sysin`) y el
orden topológico. La detección de macros que lanzan programas se reescribe sobre el frontend
nuevo en el hito 4, porque dependía del AST anterior.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

from sgm.frontend.macro_index import PathIndex, PathMatch, resolve_path


@dataclass
class GridTask:
    id: str
    kind: str  # sasgsub | sas_batch | sas_macro_step | unsupported_scheduler
    source_file: str
    line: int
    program: str | None = None  # ruta tal como aparece
    resolved_program: str | None = None
    match_status: str | None = None
    job_name: str | None = None
    queue: str | None = None
    waits: bool = False
    params: dict[str, str] = field(default_factory=dict)
    condition: str | None = None
    unknown_options: list[str] = field(default_factory=list)
    incomplete_options: list[str] = field(default_factory=list)
    after: list[str] = field(default_factory=list)  # ids de tareas de las que depende
    inferred: bool = True
    notes: list[str] = field(default_factory=list)


@dataclass
class Schedule:
    file: str
    line: int
    text: str


@dataclass
class Orchestration:
    tasks: list[GridTask] = field(default_factory=list)
    schedules: list[Schedule] = field(default_factory=list)
    order: list[str] = field(default_factory=list)


_SCHEDULE = re.compile(r"(?:Schedule|Schedule[d]?\s+by|Planificaci[oó]n)\s*:\s*(.+)", re.IGNORECASE)
_PROGRAM = re.compile(r"\.sas$", re.IGNORECASE)


def _logical_lines(text: str) -> list[tuple[int, str]]:
    out, buf, start = [], "", 0
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0] if not re.search(r"""['"].*#.*['"]""", raw) else raw
        if not buf:
            start = i
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1] + " "
            continue
        buf += line
        if buf.strip():
            out.append((start, buf.strip()))
        buf = ""
    return out


def _tokens(s: str) -> list[str]:
    try:
        return shlex.split(s)
    except ValueError:
        return s.split()


def shell_tasks(file: str, text: str, files: "list[str] | PathIndex") -> list[GridTask]:
    tasks: list[GridTask] = []
    env: dict[str, str] = {}
    for line, stmt in _logical_lines(text):
        em = re.match(r"(?:export\s+)?([A-Za-z_]\w*)=(.*)$", stmt)
        if em and not re.search(r"\bsas(gsub)?\b", em.group(2)):
            env[em.group(1)] = em.group(2).strip("'\"")
            continue
        external = re.search(r"\b(bsub|bjobs)\b", stmt)
        if external:
            tasks.append(
                GridTask(
                    id=f"{file}#{len(tasks) + 1}",
                    kind="unsupported_scheduler",
                    source_file=file,
                    line=line,
                    match_status="unsupported",
                    notes=[f"LSF command {external.group(1)} is not interpreted"],
                )
            )
            continue
        m = re.search(r"\b(sasgsub|sas)\b(?=\s)", stmt)
        if not m or not re.search(r"\.sas\b", stmt, re.IGNORECASE):
            continue
        prefix = stmt[: m.start()].strip()
        if prefix.endswith("$(") and stmt.endswith(")"):
            stmt = stmt[:-1]  # JOB=$(sasgsub ...): quitar el cierre de la sustitución
        cond = None
        if prefix and re.search(r"&&|\|\||\bif\b|\bthen\b|\[", prefix):
            cond = prefix.rstrip("&| ").strip()
            cond = "previous_success" if re.search(r'"\$\?"\s*-eq\s*0', cond) else cond
        toks = _tokens(stmt[m.start() :])
        opts: dict[str, str] = {}
        unknown: list[str] = []
        incomplete: list[str] = []
        prog = None
        params = dict(env)
        i = 1
        while i < len(toks):
            t = toks[i]
            low = t.lower()
            if low in ("-gridsubmitpgm", "-sysin") and i + 1 < len(toks):
                prog = toks[i + 1]
                i += 1
            elif low in ("-gridjobname", "-gridqueue", "-sysparm") and i + 1 < len(toks):
                opts[low] = toks[i + 1]
                i += 1
            elif low == "-set" and i + 2 < len(toks):
                params[toks[i + 1]] = toks[i + 2]
                i += 2
            elif low == "-gridsasoptions" and i + 1 < len(toks):
                for k, v in re.findall(r"-set\s+(\S+)\s+(\S+)", toks[i + 1]):
                    params[k] = v
                i += 1
            elif low == "-gridwaitresults":
                opts[low] = "1"
            elif _PROGRAM.search(t) and prog is None:
                prog = t
            elif low.startswith("-") and low not in {
                "-gridsubmitpgm",
                "-sysin",
                "-gridjobname",
                "-gridqueue",
                "-sysparm",
                "-set",
                "-gridsasoptions",
                "-gridwaitresults",
            }:
                unknown.append(t)
            elif low in {
                "-gridsubmitpgm",
                "-sysin",
                "-gridjobname",
                "-gridqueue",
                "-sysparm",
                "-set",
                "-gridsasoptions",
            }:
                incomplete.append(t)
            i += 1
        if "-sysparm" in opts:
            params["sysparm"] = opts["-sysparm"]
        kind = m.group(1) if m.group(1) == "sasgsub" else "sas_batch"
        match = resolve_path(prog, files) if prog and "$" not in prog else PathMatch("external")
        tasks.append(
            GridTask(
                id=f"{file}#{len(tasks) + 1}",
                kind=kind,
                source_file=file,
                line=line,
                program=prog,
                resolved_program=match.file if match.status == "resolved" else None,
                match_status=match.status if prog and "$" not in prog else "dynamic",
                job_name=opts.get("-gridjobname"),
                queue=opts.get("-gridqueue"),
                waits=kind == "sas_batch" or "-gridwaitresults" in opts,
                params=params,
                condition=cond,
                unknown_options=unknown,
                incomplete_options=incomplete,
            )
        )
    prev = None
    for cur in tasks:
        if cur.kind == "unsupported_scheduler":
            prev = None
            continue
        if prev and (prev.waits or cur.condition):
            cur.after = [prev.id]
        prev = cur
    return tasks


def _topological(tasks: list[GridTask]) -> list[str]:
    ids = [t.id for t in tasks]
    seen: set[str] = set()
    out: list[str] = []
    by_id = {t.id: t for t in tasks}

    def visit(i: str) -> None:
        if i in seen:
            return
        seen.add(i)
        for a in by_id[i].after:
            visit(a)
        out.append(i)

    for i in ids:
        visit(i)
    return out
