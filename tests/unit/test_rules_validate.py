"""`sgm rules validate` (F1.2): el repositorio real valida y un árbol con errores se reporta."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from sgm import rules_validate
from sgm.cli import app

ROOT = Path(__file__).resolve().parents[2]

VALID_RULE = {
    "id": "02-demo",
    "version": 1,
    "prioridad": 80,
    "description": "demo",
    "cuando": {"kind": "filter"},
    "produce": {"component": "tFilterRow"},
    "confidence": "alta",
    "alternatives": [],
    "casos": ["tests/cases/02-demo"],
}


def _tree(tmp_path: Path, rule: dict | None = None, name: str = "02-demo.yaml") -> Path:
    """Árbol mínimo con los esquemas reales y una regla de mapeo."""
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "schemas", root / "schemas")
    (root / "rules" / "mapping").mkdir(parents=True)
    (root / "rules" / "mapping" / name).write_text(
        yaml.safe_dump(rule or VALID_RULE), encoding="utf-8"
    )
    (root / "tests" / "cases" / "02-demo").mkdir(parents=True)
    case = {
        "description": "demo",
        "env": "default",
        "input": "input.sas",
        "expect": {"components": ["tFilterRow"]},
    }
    (root / "tests" / "cases" / "02-demo" / "expected.yaml").write_text(
        yaml.safe_dump(case), encoding="utf-8"
    )
    return root


def test_el_repositorio_real_valida():
    assert rules_validate.validate(ROOT) == []


def test_un_arbol_correcto_no_tiene_problemas(tmp_path: Path):
    assert rules_validate.validate(_tree(tmp_path)) == []


def test_componente_fuera_del_catalogo_se_reporta(tmp_path: Path):
    rule = {**VALID_RULE, "produce": {"component": "tInventada"}}
    problems = rules_validate.validate(_tree(tmp_path, rule))
    assert any("tInventada" in p.message and p.file.endswith("02-demo.yaml") for p in problems)


def test_caso_inexistente_se_reporta(tmp_path: Path):
    rule = {**VALID_RULE, "casos": ["tests/cases/no-existe"]}
    problems = rules_validate.validate(_tree(tmp_path, rule))
    assert any("no-existe" in p.message for p in problems)


def test_nombre_de_archivo_distinto_del_id_se_reporta(tmp_path: Path):
    problems = rules_validate.validate(_tree(tmp_path, name="otro.yaml"))
    assert any("el nombre del archivo debe ser 02-demo" in p.message for p in problems)


def test_campo_obligatorio_faltante_se_reporta_con_linea(tmp_path: Path):
    rule = {k: v for k, v in VALID_RULE.items() if k != "confidence"}
    root = _tree(tmp_path, rule)
    problems = rules_validate.validate(root)
    assert problems, "debe faltar confidence"
    assert all(p.line >= 1 for p in problems)


def test_comando_sale_con_uno_si_hay_errores(tmp_path: Path, monkeypatch):
    root = _tree(tmp_path, {**VALID_RULE, "produce": {"component": "tInventada"}})
    monkeypatch.setattr(rules_validate, "ROOT", root)
    result = CliRunner().invoke(app, ["rules", "validate"])
    assert result.exit_code == 1
    assert "tInventada" in result.output
