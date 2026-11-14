"""Asocia filerefs SAS con rutas estáticas antes de emitir los nodos de archivo."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from sgm.frontend.steps_tipos import Filename
from sgm.ir.models import Plan
from sgm.migrar.esquemas import PendienteMigracion
from sgm.redaction import redact

_CLEAR = re.compile(r"(?is)^(?:_all_\s+)?clear$")
_LITERAL = re.compile(r"(?s)^('(?:[^']|'')*'|\"(?:[^\"]|\"\")*\")(.*)$")
_METHOD = re.compile(r"(?is)^([a-z_][a-z0-9_]*)\b(?:\s+(.*))?$")


@dataclass(frozen=True)
class FilenameInfo:
    """Declaración estática de FILENAME; los campos de texto ya están saneados."""

    ref: str
    metodo: str
    destino: str
    opciones: str
    linea: int


def _literal_parts(value: str) -> tuple[str, str] | None:
    match = _LITERAL.match(value.strip())
    return (match.group(1), match.group(2).strip()) if match else None


def _contenido(literal: str) -> str:
    if len(literal) < 2 or literal[0] not in "'\"" or literal[-1] != literal[0]:
        return literal
    quote = literal[0]
    return literal[1:-1].replace(quote * 2, quote)


def _filename_info(item: Filename) -> FilenameInfo | None:
    value = redact(item.value, "").strip().rstrip(";").strip()
    if not value or _CLEAR.fullmatch(value):
        return None
    literal = _literal_parts(value)
    if literal:
        destino, opciones = literal
        return FilenameInfo(
            item.name.casefold(), "archivo", destino, redact(opciones, ""), item.line
        )

    method = _METHOD.match(value)
    if method is None:
        return FilenameInfo(item.name.casefold(), "otro", value, "", item.line)
    name = method.group(1).casefold()
    rest = (method.group(2) or "").strip()
    if name not in {"pipe", "ftp"}:
        return FilenameInfo(item.name.casefold(), "otro", value, "", item.line)
    endpoint = _literal_parts(rest)
    if endpoint:
        destino, opciones = endpoint
    else:
        destino, opciones = rest, ""
    return FilenameInfo(item.name.casefold(), name, destino, redact(opciones, ""), item.line)


def filerefs_de_programa(items: Iterable[object]) -> dict[str, FilenameInfo]:
    """Devuelve la última asociación activa; CLEAR elimina un ref y _ALL_ los elimina todos."""
    filerefs: dict[str, FilenameInfo] = {}
    for entry in items:
        item = getattr(entry, "item", entry)
        if not isinstance(item, Filename):
            continue
        ref = item.name.casefold()
        value = redact(item.value, "").strip().rstrip(";").strip()
        if _CLEAR.fullmatch(value):
            if ref == "_all_":
                filerefs.clear()
            else:
                filerefs.pop(ref, None)
            continue
        info = _filename_info(item)
        if info is not None:
            filerefs[ref] = info
    return filerefs


def _linea_operador(op) -> int | None:
    for key in ("infile_line", "file_line"):
        value = op.params.get(key)
        if isinstance(value, int):
            return value
    return op.evidence[0].line_start if op.evidence else None


def aplicar_filerefs(
    plan: Plan, filerefs: Mapping[str, FilenameInfo]
) -> tuple[Plan, list[PendienteMigracion]]:
    """Resuelve rutas literales; PIPE y referencias no cubiertas quedan pendientes."""
    pendientes: list[PendienteMigracion] = []
    for op in plan.graph.operators():
        if op.kind not in {"read_file", "write_file"}:
            continue
        ref = str(op.params.get("fileref") or "").casefold()
        if not ref:
            continue
        info = filerefs.get(ref)
        linea = _linea_operador(op)
        if info is None:
            pendientes.append(
                PendienteMigracion(
                    "P-FILEREF-SIN-DEFINIR",
                    f"{ref}: el programa no contiene una asociación FILENAME activa.",
                    linea,
                )
            )
            continue
        if info.metodo == "pipe":
            comando = _contenido(info.destino)
            pendientes.append(
                PendienteMigracion(
                    "P-FILENAME-PIPE",
                    f"FILENAME {ref} PIPE {comando!r}: el comando del sistema "
                    "no se ejecuta en el Job.",
                    info.linea,
                )
            )
            continue
        if info.metodo != "archivo" or info.opciones:
            pendientes.append(
                PendienteMigracion(
                    "P-FILENAME-METODO",
                    f"FILENAME {ref}: el método o sus opciones no están cubiertos por D2-15.",
                    info.linea,
                )
            )
            continue
        if "&" in _contenido(info.destino) or "%" in _contenido(info.destino):
            pendientes.append(
                PendienteMigracion(
                    "P-RUTA-DINAMICA",
                    f"FILENAME {ref}: la ruta depende de una macrovariable o expresión dinámica.",
                    info.linea,
                )
            )
            continue
        campo = "datafile" if op.kind == "read_file" else "outfile"
        op.params[campo] = info.destino
        op.params.pop("fileref", None)
        op.params.pop("source_dynamic", None)
    return plan, pendientes


__all__ = ["FilenameInfo", "aplicar_filerefs", "filerefs_de_programa"]
