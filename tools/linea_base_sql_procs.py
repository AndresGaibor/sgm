"""Línea base de SQL y procedimientos (plan C, tarea C-1).

Cuenta, por cada construcción de SQL o de procedimiento del corpus, cuántos casos la usan y cuántos
tienen un pendiente (según `migrar_pendientes.yaml`), agrupado por código.

Uso: uv run python tools/linea_base_sql_procs.py tests/corpus
     [--salida out/linea_base_sql_procs.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import todos_los_casos  # noqa: E402


def _es_sql_o_procedimiento(construccion: str) -> bool:
    texto = construccion.upper()
    return texto.startswith("PROC") or "SQL" in texto or "JOIN" in texto


def medir(corpus: Path) -> dict:
    """Por construcción de SQL o de procedimiento: casos que la usan y pendientes por código."""
    lista = yaml.safe_load((corpus / "migrar_pendientes.yaml").read_text(encoding="utf-8")) or {}
    casos: dict[str, int] = Counter()
    pendientes: dict[str, Counter] = {}
    for caso in todos_los_casos(corpus):
        for construccion in caso.construcciones:
            if not _es_sql_o_procedimiento(construccion):
                continue
            casos[construccion] += 1
            pendientes.setdefault(construccion, Counter())
            codigo = lista.get(caso.nombre)
            if codigo:
                pendientes[construccion][codigo] += 1
    return {
        construccion: {"casos": casos[construccion], "pendientes": dict(pendientes[construccion])}
        for construccion in sorted(casos)
    }


def _principal(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--salida", type=Path, default=REPO / "out" / "linea_base_sql_procs.json")
    args = parser.parse_args(argv)
    medida = medir(args.corpus)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(medida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(medida)} construcciones de SQL o procedimiento -> {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(_principal())
