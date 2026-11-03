"""Hechos de los pasos estructurados: DATA step, PROC SQL y PROC genérico.

Solo observa. Un conjunto de datos leído o escrito produce un hecho con su alcance; no se
decide si importa para el negocio.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from sgm.facts.model import alcance_de
from sgm.frontend.datastep import DataStep
from sgm.frontend.sql import SqlStatement
from sgm.frontend.steps import Proc, ProcSql

EXTRACTOR = "estructural"
_IO_PROCS = {
    "import": ("lectura", "entrada"),
    "download": ("lectura", "entrada"),
    "export": ("escritura", "salida"),
    "upload": ("escritura", "salida"),
}
_SQL_WRITE = {"create_table", "create_like", "insert"}
_SQL_DROP = {"drop_table", "delete"}


def _line(text_line: int, end: int | None = None) -> tuple[int, int]:
    return text_line, max(text_line, end or text_line)


def _data_step(step: DataStep, libref_externo: set[str]) -> Iterator[dict]:
    header_lines = _line(step.line)
    for name in step.outputs:
        yield _raw("tabla_escrita", name, alcance_de(name, libref_externo), header_lines)
    for stmt in step.statements:
        if stmt.kind in ("set", "merge"):
            for ref in stmt.fields.get("sources", []):
                yield _raw(
                    "tabla_leida",
                    ref["name"],
                    alcance_de(ref["name"], libref_externo),
                    _line(stmt.line),
                )
        if stmt.kind == "output" and stmt.fields.get("target"):
            name = stmt.fields["target"]
            yield _raw("tabla_escrita", name, alcance_de(name, libref_externo), _line(stmt.line))


_CREA = re.compile(r"\bcreate\s+table\s+([A-Za-z_][\w.]*)", re.I)


def _en_sentencia(stmt: SqlStatement, pos_interna: int) -> int:
    """Línea de una posición dentro del SQL interno de una sentencia.

    El SQL interno puede empezar en la línea siguiente al `(` que lo abre; contar los saltos
    desde el texto completo de la sentencia da la línea real.
    """
    base = stmt.text.find(stmt.inner_sql or "")
    desde = base + pos_interna if base >= 0 else pos_interna
    return stmt.line + stmt.text[:desde].count("\n")


_LEE_EN_MOTOR = re.compile(r"\b(?:from|join)\s+(?!connection\b)([A-Za-z_][\w.]*)", re.I)


def _sql(step: ProcSql, libref_externo: set[str]) -> Iterator[dict]:
    for stmt in step.statements:
        at = _line(stmt.line)
        if stmt.kind in _SQL_WRITE and stmt.target:
            yield _raw("tabla_escrita", stmt.target, alcance_de(stmt.target, libref_externo), at)
        if stmt.kind in _SQL_DROP and stmt.target:
            yield _raw("tabla_borrada", stmt.target, alcance_de(stmt.target, libref_externo), at)
        # Un pase directo o un `execute by` lleva SQL que corre en el motor: el `create table`
        # de un pase directo es local (el resultado vuelve a SAS); el de `execute by` es del motor.
        if stmt.kind not in _SQL_WRITE and stmt.engine:
            if stmt.kind == "execute" and stmt.inner_sql and _CREA.search(stmt.inner_sql):
                m = _CREA.search(stmt.inner_sql)
                ln = _en_sentencia(stmt, m.start())
                yield _raw("tabla_escrita", m.group(1), "externo", _line(ln), motor=stmt.engine)
            elif _CREA.search(stmt.text):
                nombre = _CREA.search(stmt.text).group(1)
                yield _raw("tabla_escrita", nombre, alcance_de(nombre, libref_externo), at)
        if stmt.inner_sql:
            for m in _LEE_EN_MOTOR.finditer(stmt.inner_sql):
                ln = _en_sentencia(stmt, m.start(1))
                yield _raw("tabla_leida", m.group(1), "externo", _line(ln), motor=stmt.engine or "")
        for source in stmt.sources:
            yield _raw("tabla_leida", source, alcance_de(source, libref_externo), at)
        if stmt.kind in ("connect", "select_passthrough", "execute") and stmt.engine:
            yield _raw("conexion_base", stmt.engine, "no_aplica", at)
        elif stmt.kind == "disconnect":
            yield _raw("sentencia_global", "disconnect", "no_aplica", at)
        elif stmt.kind == "other":
            yield _raw("desconocido", stmt.text[:80], "no_aplica", at, reason="SQL_NO_CLASIFICADO")


def _proc(step: Proc, libref_externo: set[str], text: str) -> Iterator[dict]:
    at = _line(step.line, step.end_line)
    name = step.name.lower()
    yield _raw("proc_usado", name, "no_aplica", at)
    if name in _IO_PROCS:
        uso, direccion = _IO_PROCS[name]
        path = _first_path(text)
        yield _raw(
            "archivo_externo",
            path or "(no literal)",
            "externo",
            at,
            direccion=direccion,
            uso=uso,
            procedimiento=name,
        )
    options = {k.lower(): v for k, v in step.options.items()}
    if name == "delete" and options.get("data"):
        target = options["data"]
        yield _raw("tabla_borrada", target, alcance_de(target, libref_externo), at)
    for key, tipo in (("data", "tabla_leida"), ("out", "tabla_escrita")):
        if key in options and name != "delete":
            target = options[key]
            yield _raw(tipo, target, alcance_de(target, libref_externo), at)


def _first_path(text: str) -> str | None:
    match = re.search(r"""(?:datafile|outfile|infile)\s*=\s*(['"])(.+?)\1""", text, re.I)
    return match.group(2) if match else None


def _raw(tipo: str, valor: str, alcance: str, span: tuple[int, int], **detalle: str) -> dict:
    return {
        "tipo": tipo,
        "valor": valor,
        "alcance": alcance,
        "inicio": span[0],
        "fin": span[1],
        "detalle": {k: str(v) for k, v in detalle.items()},
    }


def structural_facts(item: object, libref_externo: set[str]) -> Iterator[dict]:
    """Hechos crudos de un paso estructurado. Otros tipos de paso no producen nada aquí."""
    text = getattr(item, "text", "") or ""
    if isinstance(item, DataStep):
        yield from _data_step(item, libref_externo)
    elif isinstance(item, ProcSql):
        yield from _sql(item, libref_externo)
    elif isinstance(item, Proc):
        yield from _proc(item, libref_externo, text)
