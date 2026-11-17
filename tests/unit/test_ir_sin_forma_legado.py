"""B-6: los casos `traducible` de L1 a L3 construyen su plan sin usar la forma legado.

El contador de `ir/pasos.py` cuenta cada vez que el constructor rechaza los datos y el paso sale
con la forma anterior. Para estos casos tiene que quedar vacío.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import todos_los_casos  # noqa: E402

from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.pasos import contador_legado, reiniciar_contador_legado  # noqa: E402


def test_contador_cuenta_la_forma_legado_cuando_el_constructor_rechaza() -> None:
    from sgm.ir.models import Operator
    from sgm.ir.pasos import paso

    class _Cadena:
        def step(self, kind, params, previous, status="soportado"):
            return Operator(id="x", kind=kind, params=params)

    def rechaza():
        raise ValueError("sin datos")

    reiniciar_contador_legado()
    paso(_Cadena(), "sort", {"legado": True}, rechaza, None)
    assert contador_legado() == {"sort": 1}
    reiniciar_contador_legado()


def test_casos_traducibles_de_l1_a_l3_no_usan_la_forma_legado() -> None:
    corpus = REPO / "tests" / "corpus"
    reiniciar_contador_legado()
    casos = [
        c
        for c in todos_los_casos(corpus)
        if c.estado == "traducible" and c.nivel in ("L1", "L2", "L3")
    ]
    assert casos, "no hay casos traducibles de L1 a L3"
    for caso in casos:
        compile_file(
            analyze_program({caso.programa.name: caso.programa.read_text(encoding="utf-8")}),
            caso.programa.name,
            project_base(),
        )
    assert contador_legado() == {}, f"forma legado en {len(casos)} casos: {contador_legado()}"
