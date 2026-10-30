"""Guardia anti-sobreajuste: `src/` y `rules/` no llevan nombres propios de los scripts del cliente.

El compilador tiene que servir para cualquier programa SAS. Si alguien vuelve a escribir un nombre de
macro, tabla o variable de los scripts del cliente dentro del código o de las reglas, esta prueba falla y
muestra archivo:línea de cada coincidencia. Las reglas se escriben por estructura o comportamiento.

No distingue mayúsculas y cuenta el nombre como palabra o como parte de un identificador separado por `_`.
Los nombres del LENGUAJE SAS (proc, sleep, %put, datetime...) no están aquí: son el lenguaje, no el script.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
THIS_FILE = Path(__file__).resolve()

# Nombres propios de los scripts del cliente. Ampliar si aparecen más en `src/` o `rules/`.
FORBIDDEN_NAMES = [
    "cod1",
    "cod2",
    "cars_poc",
    "exogena",
    "split2",
    "split3",
    "executeBulkload",
    "waitForBulkLoads",
    "bulkload_generic",
]

# Dónde se busca: código Python del paquete y reglas (datos).
SEARCH_GLOBS = [
    ("src/sgm", "*.py"),
    ("rules", "*.json"),
    ("rules", "*.yaml"),
]


def _pattern() -> re.Pattern[str]:
    alternatives = "|".join(
        re.escape(name.lower()) for name in sorted(FORBIDDEN_NAMES, key=len, reverse=True)
    )
    return re.compile(r"(?<![a-z0-9])(?:" + alternatives + r")(?![a-z0-9])")


def _files() -> list[Path]:
    found: list[Path] = []
    for base, pattern in SEARCH_GLOBS:
        for path in sorted((REPO / base).rglob(pattern)):
            if "__pycache__" in path.parts or path.resolve() == THIS_FILE:
                continue
            found.append(path)
    return found


def _matches() -> list[str]:
    pattern = _pattern()
    hits: list[str] = []
    for path in _files():
        rel = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            for match in pattern.finditer(line.lower()):
                hits.append(f"{rel}:{number}: {match.group(0)}: {line.strip()[:120]}")
    return hits


def test_no_script_specific_names_in_code_or_rules():
    hits = _matches()
    assert not hits, (
        f"{len(hits)} coincidencias con nombres propios de los scripts del cliente "
        "(generalizar: quitar el nombre y tratar el patrón de forma genérica):\n" + "\n".join(hits)
    )


def test_search_scope_is_not_empty():
    # Si el alcance se queda vacío (ruta cambiada), la prueba anterior pasaría sin mirar nada.
    files = _files()
    assert any(p.suffix == ".py" for p in files)
    assert any(p.suffix == ".json" and "rules" in p.parts for p in files)
