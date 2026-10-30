"""Golden: la salida JSON del plan de tres fixtures sintéticos y del programa del cliente no cambia sin revisión.

Para regenerar las referencias después de un cambio intencional:
    SGM_UPDATE_GOLDEN=1 uv run pytest tests/unit/test_golden.py -n0
"""

import json
import os
from pathlib import Path

import pytest

from sgm.compile import compile_project
from sgm.emit.plan_json import plan_to_dict
from sgm.frontend.splitter import ZERO_WIDTH

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "sas"
GOLDEN = ROOT / "tests" / "golden"
CASES = [
    "p0_ejemplo_basico.sas",
    "p1_merge_first_last.sas",
    "generalization/etl_archivos_simple.sas",
    "client/client_poc.sas",
]


def _golden_name(rel: str) -> Path:
    return GOLDEN / (rel.replace("/", "__").removesuffix(".sas") + ".plan.json")


@pytest.mark.parametrize("rel", CASES)
def test_plan_coincide_con_la_referencia(rel):
    text = (FIXTURES / rel).read_text(encoding="utf-8", errors="replace").replace(ZERO_WIDTH, "")
    compiled, _ = compile_project({rel: text})
    current = plan_to_dict(compiled[rel].plan)
    path = _golden_name(rel)
    if os.environ.get("SGM_UPDATE_GOLDEN") == "1":
        GOLDEN.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert path.exists(), f"falta la referencia {path.name}: ejecutar con SGM_UPDATE_GOLDEN=1"
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert current == expected
