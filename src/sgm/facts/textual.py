"""Hechos de macros, sentencias globales y del texto: rutas, servidores y credenciales.

Las credenciales salen siempre como `***`. Este módulo recibe texto ya redactado, pero aun así
no copia el valor de una contraseña: el hecho guarda la máscara.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from sgm.facts.model import MASK, alcance_de
from sgm.frontend.macros import MacroDynamic
from sgm.frontend.steps import (
    Global,
    Include,
    Let,
    Libname,
    MacroCall,
    MacroDef,
    Options,
    Unparsed,
    XCommand,
)

EXTRACTOR = "textual"

_RUTA = re.compile(r"""(['"])((?:\\\\|[A-Za-z]:\\|/)[^'"\r\n]+)\1""")
_SERVIDOR = re.compile(r"\bserver\s*=\s*([A-Za-z][A-Za-z0-9_.\-]*)(?![&%\w])", re.I)
_RSUBMIT = re.compile(r"\brsubmit\s+(?!wait\b)([A-Za-z][A-Za-z0-9_.\-]*)(?![&%\w])", re.I)
_CREDENCIAL = re.compile(r"\b(?:pass|password)\s*=\s*('[^']*'|\"[^\"]*\"|[^\s;]+)", re.I)
_PWENCODE = re.compile(r"\bpwencode\b", re.I)
_MOTOR = re.compile(
    r"\b(odbc|oracle|teradata|db2|sqlsvr|postgres|mysql|impala|sasiofa|sasiox)\b", re.I
)


def libref_externos(items: list[object]) -> set[str]:
    """Bibliotecas declaradas con un motor de base de datos: cuentan como alcance `externo`."""
    refs: set[str] = set()
    for item in items:
        if isinstance(item, Libname) and _MOTOR.search(item.value or ""):
            refs.add(item.name.lower())
    return refs


def _line_of(text: str, pos: int, base: int) -> int:
    return base + text.count("\n", 0, pos)


def _scan(text: str, base: int, end: int) -> Iterator[dict]:
    for m in _RUTA.finditer(text):
        ln = _line_of(text, m.start(), base)
        yield _raw("ruta_literal", m.group(2), "no_aplica", ln, ln, uso=_uso(text))
    for m in _SERVIDOR.finditer(text):
        ln = _line_of(text, m.start(), base)
        yield _raw("servidor", m.group(1), "no_aplica", ln, ln)
    for m in _RSUBMIT.finditer(text):
        ln = _line_of(text, m.start(), base)
        yield _raw("servidor", m.group(1), "no_aplica", ln, ln, origen="rsubmit")
    for m in _CREDENCIAL.finditer(text):
        ln = _line_of(text, m.start(), base)
        yield _raw("credencial", MASK, "no_aplica", ln, ln)
    for m in _PWENCODE.finditer(text):
        ln = _line_of(text, m.start(), base)
        yield _raw("credencial", MASK, "no_aplica", ln, ln, origen="pwencode")


def _uso(text: str) -> str:
    low = text.lower()
    if "infile" in low or "import" in low:
        return "lectura"
    if "outfile" in low or "export" in low or "upload" in low:
        return "escritura"
    return "no_aplica"


def _raw(tipo: str, valor: str, alcance: str, ini: int, fin: int, **detalle: str) -> dict:
    return {
        "tipo": tipo,
        "valor": valor,
        "alcance": alcance,
        "inicio": ini,
        "fin": fin,
        "detalle": {k: str(v) for k, v in detalle.items()},
    }


def textual_facts(item: object, libref_externo: set[str]) -> Iterator[dict]:
    """Hechos de un paso de macro, sentencia global o texto."""
    text = getattr(item, "text", "") or ""
    base = int(getattr(item, "line", 1) or 1)
    end = int(getattr(item, "end_line", base) or base)
    if isinstance(item, MacroDef):
        yield _raw(
            "macro_definida", item.name, "no_aplica", base, end, params=",".join(item.params)
        )
    elif isinstance(item, MacroCall):
        yield _raw("macro_llamada", item.name, "no_aplica", base, end, args=item.args or "")
    elif isinstance(item, Let):
        dinamica = "%" in item.value or "&" in item.value
        tipo = "variable_dinamica" if dinamica else "variable_constante"
        yield _raw(tipo, item.name, "no_aplica", base, end, valor_sas=item.value[:120])
    elif isinstance(item, Include):
        path = item.path or "(no literal)"
        yield _raw("include_externo", path, "externo", base, end)
    elif isinstance(item, Libname):
        alcance = alcance_de(f"{item.name}.x", libref_externos([item]))
        yield _raw("biblioteca", item.name, alcance, base, end, destino=item.value[:120])
    elif isinstance(item, Options):
        yield _raw("sentencia_global", "options", "no_aplica", base, end)
    elif isinstance(item, Global):
        word = (text.strip().split() or ["global"])[0].lower()[:40]
        yield _raw("sentencia_global", word, "no_aplica", base, end)
    elif isinstance(item, XCommand):
        yield _raw("comando_sistema", item.command[:80], "no_aplica", base, end)
    elif isinstance(item, Unparsed):
        yield _raw("desconocido", text[:80], "no_aplica", base, end, reason=item.reason)
    elif isinstance(item, MacroDynamic):
        yield _raw("desconocido", text[:80], "no_aplica", base, end, reason=item.reason)
    for fragmento, linea in _fragmentos(item):
        yield from _scan(fragmento, linea, linea)


def _fragmentos(item: object) -> Iterator[tuple[str, int]]:
    """Texto del paso y de cada una de sus sentencias, cada uno con su línea real.

    Un `PROC SQL` guarda su cabecera en `text`; el `connect` y las consultas están en
    `statements`. Escanear solo `text` dejaría fuera credenciales y servidores.
    """
    yield (getattr(item, "text", "") or ""), int(getattr(item, "line", 1) or 1)
    for stmt in getattr(item, "statements", None) or []:
        yield (getattr(stmt, "text", "") or ""), int(getattr(stmt, "line", 1) or 1)
