"""Línea base del plan lógico sobre el corpus `traducible` (B-1, MG-P1 y L6).

Por cada caso `traducible` compila su programa y cuenta operadores, cuántos quedan `soportado`,
los no migrados y los pendientes por código. No mide los constructores de `ir/operadores.py`
(eso es B-5 y B-6); la columna «construidos por constructor» queda fuera a propósito.

Uso: uv run python tools/linea_base_plan_logico.py [carpeta-del-corpus]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))

import tempfile  # noqa: E402

from corpus_lib.caso import todos_los_casos  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.models import Plan  # noqa: E402

CORPUS_POR_DEFECTO = RAIZ / "tests" / "corpus"
SALIDA = RAIZ / "out" / "linea_base_plan_logico.json"


def medir_plan(plan: Plan) -> dict:
    operadores = plan.graph.operators()
    return {
        "operadores": len(operadores),
        "soportados": sum(1 for op in operadores if op.status == "soportado"),
        "no_migrados": len(plan.not_migrated),
    }


def medir_programa(texto: str, nombre: str = "programa.sas") -> dict:
    """Mide un programa SAS suelto; lo usan las pruebas y `medir`."""
    analisis = analyze_program({nombre: texto})
    plan = compile_file(analisis, nombre, project_base()).plan
    return medir_plan(plan)


def codigos_de_programa(programa: Path, muestra: Path | None = None) -> Counter:
    """Pendientes por código que `sgm migrar` emite para un programa."""
    resultado = migrar(programa, Path(tempfile.mkdtemp(prefix="linea_base_")), muestra=muestra)
    return Counter(p.codigo for p in resultado.pendientes)


def medir(corpus: Path) -> dict:
    """Cifras del plan y pendientes con su código `P-…` (los que emite `sgm migrar`)."""
    total = {"casos": 0, "operadores": 0, "soportados": 0, "no_migrados": 0}
    pendientes: Counter = Counter()
    por_nivel: dict[str, int] = {}
    for caso in todos_los_casos(corpus):
        if caso.estado != "traducible":
            continue
        salida = Path(tempfile.mkdtemp(prefix="linea_base_"))
        resultado = migrar(caso.programa, salida, muestra=caso.entradas)
        m = medir_programa(caso.programa.read_text(encoding="utf-8"), caso.programa.name)
        total["casos"] += 1
        for clave in ("operadores", "soportados", "no_migrados"):
            total[clave] += m[clave]
        pendientes.update(p.codigo for p in resultado.pendientes)
        por_nivel[caso.nivel] = por_nivel.get(caso.nivel, 0) + 1
    return {
        **total,
        "por_nivel": dict(sorted(por_nivel.items())),
        "pendientes": dict(pendientes.most_common()),
    }


def main(argv: list[str]) -> int:
    corpus = Path(argv[0]) if argv else CORPUS_POR_DEFECTO
    resultado = medir(corpus)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    print(f"escrito: {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
