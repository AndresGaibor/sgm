"""Modelo del flujo de un programa SAS: pasos en orden, y qué dataset lee y escribe cada uno.

Es una vista de cómo funciona el programa, no una traducción: cada paso conserva su línea y un
extracto de su texto. Un dataset que un paso lee se une al último paso anterior que lo escribió.
Si ningún paso anterior lo escribió, es una entrada externa del programa.

Las credenciales se enmascaran antes de analizar, así ningún extracto las lleva en claro.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.flow.pasos_archivo import entradas_salidas_data_step, lecturas_escrituras_proc
from sgm.frontend.datastep import DataStep
from sgm.frontend.macros_modelo import MacroDynamic
from sgm.frontend.program import ProgramAnalysis, ProgramItem, analyze_program
from sgm.frontend.steps_tipos import (
    Global,
    Include,
    Let,
    Libname,
    MacroCall,
    MacroDef,
    Options,
    Proc,
    ProcSql,
    Unparsed,
    XCommand,
)
from sgm.redaction import redact

EXTRACTO_MAX_LINEAS = 14
DIAGRAMA_POR_PASO_MAX = 200  # por encima de este número de pasos, el diagrama usa secciones
SECCION_SIN_NOMBRE = "(sin sección)"
ENTRADA_EXTERNA = "Entrada externa"
MOTIVO_DINAMICO = (
    "depende de valores que solo se conocen al ejecutar: no se puede seguir su flujo sin correrlo"
)
_CONFIG_TYPES = (Libname, Let, Options, Include, Global, MacroDef, MacroCall, XCommand)


@dataclass
class FlowStep:
    """Un paso del programa, o una entrada externa, con sus datasets."""

    id: str
    file: str
    line: int
    label: str | None
    kind: str  # "data", "sql", "proc", "external", "dynamic", "unparsed"
    type_name: str  # "DATA step", "PROC SQL", "PROC SORT", "Entrada externa", ...
    title: str
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    excerpt: str = ""
    macro_call: str | None = None
    outer_call: str | None = None  # llamada más externa, la que escribió el usuario
    layer: int = 0


@dataclass
class FlowEdge:
    source: str
    target: str
    dataset: str


@dataclass
class ConfigLine:
    kind: str  # "libname", "%let", "options", "%include", "macro", ...
    line: int
    text: str


@dataclass
class Pending:
    """Algo que no se pudo seguir: su texto y el paso al que se refiere, si lo hay."""

    text: str
    step_id: str | None


@dataclass
class FlowModel:
    program: str
    steps: list[FlowStep]
    inputs: list[FlowStep]
    edges: list[FlowEdge]
    external_inputs: list[str]
    config: list[ConfigLine]
    pending: list[Pending]


def dataset_key(name: str) -> str:
    """Nombre de dataset para comparar: sin mayúsculas y sin el prefijo WORK. de la biblioteca."""
    low = name.strip().lower()
    return low[5:] if low.startswith("work.") else low


def _excerpt(lines: list[str]) -> str:
    """Primeras líneas del paso; si el paso es más largo, se corta con una marca."""
    shown = [line for line in lines if line.strip()][:EXTRACTO_MAX_LINEAS]
    text = "\n".join(shown)
    return text + ("\n..." if len(lines) > EXTRACTO_MAX_LINEAS else "")


def _data_step(obj: DataStep) -> tuple[str, str, list[str], list[str], list[str], list[str]]:
    reads, writes = entradas_salidas_data_step(obj)
    title = "DATA " + ", ".join(obj.outputs) if obj.outputs else "DATA step"
    lines = [obj.text] + [st.text for st in obj.statements]
    return "DATA step", title, reads, writes, [], lines


def _sql_step(obj: ProcSql) -> tuple[str, str, list[str], list[str], list[str], list[str]]:
    reads: list[str] = []
    writes: list[str] = []
    notes: list[str] = []
    for st in obj.statements:
        reads.extend(st.sources)
        if st.kind in ("create_table", "create_like", "insert") and st.target:
            writes.append(st.target)
        elif st.kind == "delete" and st.target:
            notes.append(f"borra filas de {st.target}")
        elif st.kind == "drop_table" and st.target:
            notes.append(f"elimina la tabla {st.target}")
        elif st.kind == "select_passthrough":
            notes.append(f"consulta directa al motor {st.engine}")
            if st.target:
                writes.append(st.target)
        elif st.kind == "execute":
            notes.append(f"ejecuta SQL en el motor {st.engine}")
    creates = [st.target for st in obj.statements if st.kind == "create_table" and st.target]
    title = f"PROC SQL: crea {creates[0]}" if creates else "PROC SQL"
    lines = [obj.text] + [st.text for st in obj.statements]
    return "PROC SQL", title, reads, writes, notes, lines


def _proc_step(obj: Proc) -> tuple[str, str, list[str], list[str], list[str], list[str]]:
    reads, writes = lecturas_escrituras_proc(obj.name, obj.text)
    notes: list[str] = []
    if obj.name == "sort" and not writes and reads:
        writes = list(reads)
        notes.append("ordena el dataset en su lugar (sin OUT=)")
    type_name = f"PROC {obj.name.upper()}"
    return type_name, type_name, reads, writes, notes, [obj.text, *obj.body]


def _step_parts(item: ProgramItem) -> tuple | None:
    """Tipo, título, lectura, escritura, notas y extracto de un paso. None si es configuración."""
    obj = item.item
    if isinstance(obj, DataStep):
        return _data_step(obj)
    if isinstance(obj, ProcSql):
        return _sql_step(obj)
    if isinstance(obj, Proc):
        return _proc_step(obj)
    if isinstance(obj, MacroDynamic):
        return (
            "Macro dinámica",
            obj.detail or "Código que depende de la ejecución",
            [],
            [],
            [MOTIVO_DINAMICO],
            [obj.text],
        )
    if isinstance(obj, Unparsed):
        return ("Sin leer", obj.reason, [], [], [], [obj.text])
    return None


def _config_line(item: ProgramItem) -> ConfigLine | None:
    obj = item.item
    if not isinstance(obj, _CONFIG_TYPES):
        return None
    kinds = {
        Libname: "libname",
        Let: "%let",
        Options: "options",
        Include: "%include",
        Global: "global",
        MacroDef: "%macro",
        MacroCall: "llamada de macro",
        XCommand: "%sysexec",
    }
    kind = kinds[type(obj)]
    text = getattr(obj, "text", "") or getattr(obj, "command", "")
    return ConfigLine(kind, item.line, text.strip()[:200])


def assign_layers(steps: list[FlowStep], edges: list[FlowEdge]) -> None:
    """Capa de cada paso: 1 + la capa de su predecesor más lejano. Las entradas van en la capa 0."""
    incoming: dict[str, list[str]] = {}
    for edge in edges:
        incoming.setdefault(edge.target, []).append(edge.source)
    depth: dict[str, int] = {}
    for step in steps:
        preds = incoming.get(step.id, [])
        depth[step.id] = 1 + max((depth.get(p, 0) for p in preds), default=0)
        step.layer = depth[step.id]


def build_flow(
    program: str, items: list[ProgramItem], unresolved: list[tuple[str, str, str]]
) -> FlowModel:
    """Modelo del flujo de un programa a partir de sus pasos ya analizados, en orden de línea."""
    steps: list[FlowStep] = []
    config: list[ConfigLine] = []
    for item in items:
        parts = _step_parts(item)
        if parts is None:
            line = _config_line(item)
            if line:
                config.append(line)
            continue
        type_name, title, reads, writes, notes, lines = parts
        kind = {
            "DATA step": "data",
            "PROC SQL": "sql",
            "Macro dinámica": "dynamic",
            "Sin leer": "unparsed",
        }.get(type_name, "proc")
        steps.append(
            FlowStep(
                id=f"p{len(steps) + 1}",
                file=item.file,
                line=item.line,
                label=item.label,
                kind=kind,
                type_name=type_name,
                title=title,
                reads=reads,
                writes=writes,
                notes=notes,
                excerpt=_excerpt(lines),
                macro_call=item.call,
                outer_call=item.outer_call,
            )
        )
    edges: list[FlowEdge] = []
    inputs: dict[str, FlowStep] = {}
    external: list[str] = []
    for index, step in enumerate(steps):
        for name in dict.fromkeys(step.reads):
            key = dataset_key(name)
            producer = next(
                (
                    prev
                    for prev in reversed(steps[:index])
                    if key in {dataset_key(w) for w in prev.writes}
                ),
                None,
            )
            if producer is not None:
                edges.append(FlowEdge(producer.id, step.id, name))
                continue
            if key not in inputs:
                inputs[key] = FlowStep(
                    id=f"e{len(inputs) + 1}",
                    file=step.file,
                    line=step.line,
                    label=None,
                    kind="external",
                    type_name=ENTRADA_EXTERNA,
                    title=name,
                    writes=[name],
                )
                external.append(name)
            edges.append(FlowEdge(inputs[key].id, step.id, name))
    assign_layers(steps, edges)
    pending = [
        Pending(f"%include sin resolver en {file}: {raw} ({status})", None)
        for file, raw, status in unresolved
    ]
    pending += [
        Pending(f"{s.file}:{s.line} {s.type_name}: {s.title}", s.id)
        for s in steps
        if s.kind in ("dynamic", "unparsed")
    ]
    return FlowModel(program, steps, list(inputs.values()), edges, external, config, pending)


def build_flows(
    files: dict[str, str], externals: dict[str, str] | None = None
) -> dict[str, FlowModel]:
    """Un modelo por programa. Redacta credenciales antes de analizar."""
    # El BOM UTF-8 se quita: si queda pegado, la primera palabra (`data`) no se reconoce.
    clean = {path: redact(text.lstrip("\ufeff"), path) for path, text in files.items()}
    ext = {path: redact(text, path) for path, text in (externals or {}).items()}
    analysis: ProgramAnalysis = analyze_program(clean, ext)
    return {
        program: build_flow(
            program,
            [item for item in analysis.items if item.file == program],
            [u for u in analysis.unresolved_includes if u[0] == program],
        )
        for program in sorted(clean)
    }
