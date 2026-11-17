"""B-16: un `DO WHILE`/`DO UNTIL` de datos no es fontanería de espera. Antes, el patrón `espera` de
`rules/sas/plumbing.yaml` lo tomaba por sondeo de procesos y lo quitaba del plan sin aviso."""

from __future__ import annotations

import pytest

from sgm.passes.plumbing_patterns import match_plumbing


@pytest.mark.parametrize(
    "sentencia",
    ["DO WHILE (x1 < 5);", "do while(trend{i} < y);", "DO UNTIL (x > 1);", "do   until (n>3);"],
)
def test_do_while_y_until_no_son_espera(sentencia: str) -> None:
    assert match_plumbing(sentencia) is None


@pytest.mark.parametrize(
    "sentencia",
    ["until ps -ef | grep x; do sleep 5; done", "while ps -p $pid; do sleep 1; done", "sleep(5);"],
)
def test_la_espera_de_shell_sigue_siendo_fontaneria(sentencia: str) -> None:
    coincide = match_plumbing(sentencia)
    assert coincide is not None and coincide.category == "espera"
