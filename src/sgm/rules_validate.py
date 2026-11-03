"""Validación de reglas y configuración (F1.2): `sgm rules validate`.

Cada archivo se revisa con el esquema de su tipo (`schemas/rules/`). Además:
- cada `tests` de una regla apunta a una carpeta de `tests/cases/` que tiene `expected.yaml`;
- cada componente de `rules/mapping/` existe en el catálogo de Talend (salvo `engine:...`);
- el nombre del archivo de una regla es su `id`.

Un error sale con archivo, ruta del campo y línea (la línea se busca por el nombre del campo).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema
import yaml

from sgm.catalog.talend import component_names

ROOT = Path(__file__).resolve().parents[2]

# Carpeta o archivo de reglas -> tipo de esquema.
RULE_FOLDERS = {
    "rules/mapping": "mapping",
    "rules/sas/procs": "proc",
    "rules/sas/statements": "statement",
    "rules/sas/functions": "function",
    "rules/sas/intrinsics": "intrinsic",
    "rules/sas/catalogo": "catalogo",
}
RULE_FILES = {
    "rules/sas/informats.yaml": "informats",
    "rules/sas/plumbing.yaml": "plumbing",
    "rules/routing.yaml": "routing",
}
ENV_FILES = {
    "env/engines.json": "engines",
    "env/project.json": "project",
    "env/externals.json": "externals",
}


@dataclass(frozen=True)
class Problem:
    file: str
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.path}] {self.message}"


def _schema(name: str, root: Path) -> dict:
    return json.loads((root / "schemas" / "rules" / f"{name}.schema.json").read_text("utf-8"))


def _load(path: Path):
    text = path.read_text(encoding="utf-8")
    data = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    return data, text


def _line_of(text: str, key: str | None) -> int:
    if key:
        for number, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith((f"{key}:", f'"{key}":')):
                return number
    return 1


def _check_schema(rel: str, data, text: str, schema: dict) -> list[Problem]:
    problems = []
    for error in jsonschema.Draft202012Validator(schema).iter_errors(data):
        fields = list(error.absolute_path)
        key = next((str(p) for p in reversed(fields) if isinstance(p, str)), None)
        path = "/".join(str(p) for p in fields) or "(raíz)"
        problems.append(Problem(rel, path, _line_of(text, key), error.message))
    return problems


def _check_rule(
    rel: str, path: Path, data, text: str, schema_name: str, root: Path
) -> list[Problem]:
    problems = _check_schema(rel, data, text, _schema(schema_name, root))
    if not isinstance(data, dict):
        return problems
    if "id" in data and path.stem != data["id"]:
        message = f"el nombre del archivo debe ser {data['id']}"
        problems.append(Problem(rel, "id", _line_of(text, "id"), message))
    # `casos` es el nombre del formato por hechos (fase 2); `tests` se acepta en los demás tipos.
    campo = "casos" if "casos" in data else "tests"
    for test in data.get(campo, []) or []:
        if not (root / test / "expected.yaml").exists():
            message = f"el caso {test} no existe"
            problems.append(Problem(rel, campo, _line_of(text, campo), message))
    component = (data.get("produce") or data.get("emit") or {}).get("component")
    known = component_names()
    if isinstance(component, str) and component != "none" and not component.startswith("engine:"):
        if component not in known:
            message = f"{component} fuera del catálogo de Talend"
            problems.append(Problem(rel, "emit/component", _line_of(text, "component"), message))
    return problems


def _yaml_files(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.yaml")) if folder.is_dir() else []


def validate(root: Path | None = None) -> list[Problem]:
    """Problemas de reglas, casos y configuración de `root`. Lista vacía si todo valida."""
    root = ROOT if root is None else root
    problems: list[Problem] = []
    for folder, schema_name in RULE_FOLDERS.items():
        for path in _yaml_files(root / folder):
            data, text = _load(path)
            rel = path.relative_to(root).as_posix()
            problems += _check_rule(rel, path, data, text, schema_name, root)
    for rel, schema_name in RULE_FILES.items():
        path = root / rel
        if path.exists():
            data, text = _load(path)
            problems += _check_rule(rel, path, data, text, schema_name, root)
    cases = root / "tests" / "cases"
    for path in sorted(cases.glob("*/expected.yaml")) if cases.is_dir() else []:
        data, text = _load(path)
        rel = path.relative_to(root).as_posix()
        problems += _check_schema(rel, data, text, _schema("case", root))
    for rel, schema_name in ENV_FILES.items():
        path = root / rel
        if path.exists():
            data, text = _load(path)
            problems += _check_schema(rel, data, text, _schema(schema_name, root))
    return problems
