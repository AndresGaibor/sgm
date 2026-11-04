"""Reconocimiento de la región de carga: qué hace cada paso y cómo crece la región.

Un paso pertenece a la región si es maquinaria de carga (fontanería, configuración, preparación de
macro variables o de tablas, troceo en sesiones, limpieza). Para decidirlo se miran las macro
variables y los datasets que cada paso define y usa, en el orden del programa.

- `FactBook`: lo que sabe la pasada de cada operador (lanzamiento, espera, definiciones, usos).
- `Flow`: dónde se define y se usa cada nombre, para saber si una definición la lee la región.
- `grow`: amplía la región hacia atrás y hacia delante, por unidades (los pasos de un mismo origen).
"""

from __future__ import annotations

import re
from bisect import bisect_right
from dataclasses import dataclass, field

from sgm.ir.models import Operator
from sgm.passes import p02_plumbing

MAX_LOOKAROUND = 40  # unidades que se miran a cada lado de la región
_LAUNCH = re.compile(r"&\s*[\"']")  # comando en segundo plano dentro de un literal: "... &"
_WAIT = re.compile(r"(?is)\buntil\b.*\bwc\s+-l\b|\bps\b.*\bwc\s+-l\b")
_MACRO_USE = re.compile(r"&(\w+)")
_MACRO_DEFS = (
    re.compile(r"(?i)%let\s+(\w+)"),
    re.compile(r"(?i)%do\s+(\w+)\s*="),
    re.compile(r"(?i)\bsymputx?\(\s*['\"](\w+)"),
    re.compile(r"(?i)\binto\s*:\s*(\w+)"),
    re.compile(r"(?i)%syslput\s+(\w+)\s*="),
)
_GLOBAL = re.compile(r"(?i)%global\s+([^;]*)")
_DATA_REF = re.compile(r"(?i)\bdata\s*=\s*([\w.]+)")
RSUBMIT_OPEN = re.compile(r"(?im)^\s*rsubmit\b")
RSUBMIT_CLOSE = re.compile(r"(?i)\bendrsubmit\b")
_OUT_REF = re.compile(r"(?i)\bout\s*=\s*([\w.]+)")


def _dname(name: str) -> str:
    """Nombre de dataset en minúsculas, sin `work.` (WORK es la biblioteca por defecto)."""
    clean = name.strip().lower()
    return clean[5:] if clean.startswith("work.") else clean


def _macro_of(name: str) -> str | None:
    """`&cmdt.` como nombre de dataset es una macro variable: devuelve `cmdt`."""
    clean = name.strip().lower()
    return clean[1:].rstrip(".") if clean.startswith("&") else None


@dataclass(frozen=True)
class Facts:
    """Lo que la pasada necesita saber de un operador. Se calcula una vez por operador."""

    launch: bool
    wait: bool
    defs: frozenset[tuple[str, str]]  # ("m", macro) o ("d", dataset)
    uses: frozenset[tuple[str, str]]
    fontaneria: bool  # fontanería o configuración: no transforma datos
    call: str | None  # invocación de macro de origen


class FactBook:
    def __init__(self) -> None:
        self._memo: dict[str, Facts] = {}

    def of(self, op: Operator) -> Facts:
        found = self._memo.get(op.id)
        if found is None:
            found = self._compute(op)
            self._memo[op.id] = found
        return found

    def mark_remote(self, seq: list[Operator]) -> None:
        """Lo que va entre `rsubmit` y `endrsubmit` corre en otra sesión: sus datasets no son
        locales. Conserva las macro variables (la sesión remota las recibe por %syslput)."""
        inside = False
        for op in seq:
            text = p02_plumbing.op_text(op)
            if RSUBMIT_OPEN.search(text):
                inside = True
            if inside:
                fact = self.of(op)
                self._memo[op.id] = Facts(
                    launch=fact.launch,
                    wait=fact.wait,
                    defs=frozenset(d for d in fact.defs if d[0] == "m"),
                    uses=frozenset(u for u in fact.uses if u[0] == "m"),
                    fontaneria=True,
                    call=fact.call,
                )
            if RSUBMIT_CLOSE.search(text):
                inside = False

    @staticmethod
    def _compute(op: Operator) -> Facts:
        text = p02_plumbing.op_text(op)
        defs = {("m", m.lower()) for pattern in _MACRO_DEFS for m in pattern.findall(text)}
        for group in _GLOBAL.findall(text):
            defs |= {("m", name.lower()) for name in group.split()}
        names = [str(n) for n in op.params.get("outputs", []) if isinstance(n, str)]
        if op.kind in ("write", "write_file") and op.params.get("dataset"):
            names.append(str(op.params["dataset"]))
        names += _OUT_REF.findall(text)
        defs |= _names(names)
        uses = {("m", m.lower()) for m in _MACRO_USE.findall(text)}
        names = [str(n) for key in ("inputs", "sources") for n in op.params.get(key, [])]
        if op.kind in ("read", "read_file") and op.params.get("dataset"):
            names.append(str(op.params["dataset"]))
        names += _DATA_REF.findall(text)
        uses |= _names(names)
        fontaneria = "plumbing" in op.params or op.params.get("reason") == "CONFIGURACION"
        call = op.evidence[0].call if op.evidence else None
        return Facts(
            launch=bool(_LAUNCH.search(text)),
            wait=bool(_WAIT.search(text)),
            defs=frozenset(defs),
            uses=frozenset(uses),
            fontaneria=fontaneria,
            call=call,
        )


def _names(names: list[str]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for name in names:
        macro = _macro_of(name)
        keys.add(("m", macro) if macro is not None else ("d", _dname(name)))
    return keys


@dataclass
class Flow:
    """Dónde se define y dónde se usa cada macro variable y cada dataset, por índice.

    Los bloques repetidos del programa reutilizan los mismos nombres. Por eso una definición solo
    tiene como consumidores los usos que están antes de su siguiente redefinición.
    """

    seq: list[Operator]
    facts: FactBook
    params: dict[str, list[str]] = field(default_factory=dict)  # macro -> parámetros
    pos: dict[str, int] = field(default_factory=dict)
    uses: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    users: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    defs: dict[tuple[str, str], list[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        previous_call: str | None = None
        for i, op in enumerate(self.seq):
            self.pos[op.id] = i
            fact = self.facts.of(op)
            if fact.call is not None and fact.call != previous_call:
                # Al empezar una invocación, sus parámetros toman el valor que les pasa el llamador.
                callee = fact.call.rsplit(":", 1)[-1].lower()
                for name in self.params.get(callee, []):
                    self.defs.setdefault(("m", name), []).append(i)
            previous_call = fact.call
            for key in fact.uses:
                self.uses.setdefault(key, []).append(i)
                self.users.setdefault(key, []).append(op.id)
            for key in fact.defs:
                self.defs.setdefault(key, []).append(i)

    def live_users(self, key: tuple[str, str], index: int) -> set[str]:
        """Operadores que usan `key` entre la definición en `index` y la siguiente redefinición."""
        defs = self.defs.get(key, [])
        at = bisect_right(defs, index)
        nxt = defs[at] if at < len(defs) else len(self.seq) + 1
        uses = self.uses.get(key, [])
        lo = bisect_right(uses, index)
        hi = bisect_right(uses, nxt - 1)
        return set(self.users.get(key, [])[lo:hi])


def absorbable(unit: list[Operator], region: list[Operator], flow: Flow) -> bool:
    """Si la unidad puede entrar en la región (ver el docstring del módulo)."""
    facts = flow.facts
    if any(facts.of(op).launch or facts.of(op).wait for op in unit):
        return False
    inside = {o.id for o in region} | {op.id for op in unit}
    region_ids = {o.id for o in region}
    region_calls = {facts.of(o).call for o in region} - {None}
    fontaneria = all(facts.of(op).fontaneria for op in unit)
    macro_consumed = False  # una macro variable de preparación que la región lee
    data_consumed = False  # un dataset que la región lee: es la entrada de la carga, no entra
    for op in unit:
        index = flow.pos[op.id]
        for key in facts.of(op).defs:
            live = flow.live_users(key, index)
            if live - inside:  # alguien fuera de la región lee lo que esta unidad define
                return False
            if live & region_ids:
                if key[0] == "m":
                    macro_consumed = True
                else:
                    data_consumed = True
    # Misma invocación de macro que la región: preparación o troceo de la propia carga (un paso
    # DATA partido en varios items, o una tabla auxiliar que nadie lee después).
    same_call = any(facts.of(op).call in region_calls for op in unit)
    if data_consumed and not (fontaneria or same_call):
        return False
    if fontaneria or same_call or macro_consumed:
        return True
    defined = [key for op in unit for key in facts.of(op).defs]
    if any(kind == "d" for kind, _ in defined):
        return False  # un dataset que nadie de la región lee: es cálculo del programa, no carga
    if defined:
        return True  # macro variable de preparación que nadie lee
    # Sin definiciones: solo una sentencia de macro que usa algo que la región define.
    region_defs: set[tuple[str, str]] = set()
    for other in region:
        region_defs |= facts.of(other).defs
    unit_uses: set[tuple[str, str]] = set()
    for op in unit:
        unit_uses |= facts.of(op).uses
    macro_level = all(op.kind == "unsupported" for op in unit)
    return macro_level and bool(unit_uses & region_defs)


def units(seq: list[Operator]) -> list[tuple[int, int]]:
    """Rangos [inicio, fin] de los operadores de cada paso, en orden."""

    def key(op: Operator) -> tuple:
        if not op.evidence:
            return (op.id,)
        ev = op.evidence[0]
        return (ev.file, ev.line_start, ev.line_end, ev.call)

    units: list[tuple[int, int]] = []
    start = 0
    for i in range(1, len(seq) + 1):
        if i == len(seq) or key(seq[i]) != key(seq[start]):
            units.append((start, i - 1))
            start = i
    return units


def grow(seq, units, first: int, last: int, floor: int, ceiling: int, flow: Flow):
    """Amplía las unidades [first, last] hacia atrás (sin bajar de `floor`) y hacia delante (sin
    llegar a `ceiling`). Un vecino lejano entra con todo lo que hay entre él y la región, porque
    sus consumidores pueden estar en esa franja. Cada unidad de la franja debe ser absorbible con
    la región tentativa que la contiene. Devuelve el nuevo rango."""

    def ops_of(k: int) -> list[Operator]:
        a, b = units[k]
        return seq[a : b + 1]

    def span(a: int, b: int) -> list[Operator]:
        return [op for k in range(a, b + 1) for op in ops_of(k)]

    # `absorbable` solo depende de la unidad y del rango de la región que la contiene: se memoiza
    # para no rehacer la región (miles de operadores) en cada iteración de `grow`.
    back_memo: dict[tuple[int, int], bool] = {}
    forward_memo: dict[tuple[int, int, int], bool] = {}

    def back_ok(k: int) -> bool:
        for j in range(k, first):
            key = (j, last)
            verdict = back_memo.get(key)
            if verdict is None:
                verdict = absorbable(ops_of(j), span(j + 1, last), flow)
                back_memo[key] = verdict
            if not verdict:
                return False
        return True

    def forward_ok(k: int) -> bool:
        group = span(first, k)
        for j in range(last + 1, k + 1):
            key = (j, first, k)
            verdict = forward_memo.get(key)
            if verdict is None:
                verdict = absorbable(ops_of(j), group, flow)
                forward_memo[key] = verdict
            if not verdict:
                return False
        return True

    changed = True
    while changed:
        changed = False
        for k in range(first - 1, max(floor, first - MAX_LOOKAROUND) - 1, -1):
            if back_ok(k):
                first, changed = k, True
                break
        if changed:
            continue
        for k in range(last + 1, min(ceiling, last + MAX_LOOKAROUND + 1)):
            if forward_ok(k):
                last, changed = k, True
                break
    return first, last
