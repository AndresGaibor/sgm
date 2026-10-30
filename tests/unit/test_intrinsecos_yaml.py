"""Intrínsecos declarados en `rules/sas/intrinsics/` (F1.4): el `implementation` existe."""

import importlib

import yaml

from sgm.passes.plumbing_patterns import ROOT

INTRINSICS = ROOT / "rules" / "sas" / "intrinsics"


def test_cada_implementacion_declarada_existe():
    for path in sorted(INTRINSICS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        modulo, _, funcion = data["implementation"].rpartition(".")
        assert callable(getattr(importlib.import_module(modulo), funcion)), path.name
