"""Configuración del entorno y del proyecto (`env/`), con validación al cargarla.

- `engines.json`: DSN, bibliotecas y esquemas que apuntan a un motor (por ejemplo `impala`).
- `project.json`: políticas del proyecto (ubicación, reportes, tamaño máximo de un Job).
- `externals.json`: `%include` de archivos que están fuera del repositorio. Un archivo declarado
  aquí no genera hueco: sus variables pasan a ser contexto del Job.
- `externals/*.sas`: archivos externos presentes. Se leen como cualquier fuente del proyecto.

Un archivo ausente usa sus valores por defecto. Un archivo presente con una forma incorrecta falla
con un mensaje que nombra el archivo y el campo. Ningún valor se inventa: los que el código SAS no
demuestra no se agregan.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PLACEMENTS = frozenset({"push_to_db", "flow"})
REPORTS = frozenset({"discard", "log", "csv"})
_ENGINE = re.compile(r"^[a-z][a-z0-9_]*$")
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ENV_DIR = Path(__file__).resolve().parents[3] / "env"


class ConfigError(ValueError):
    """Un archivo de configuración no tiene la forma esperada."""


@dataclass(frozen=True)
class Engines:
    dsn: dict[str, str] = field(default_factory=dict)  # nombre DSN -> motor
    libraries: dict[str, str] = field(default_factory=dict)  # biblioteca -> motor
    db_schemas: dict[str, str] = field(default_factory=dict)  # esquema -> motor

    def library_engines(self) -> dict[str, str]:
        """Biblioteca o esquema (en mayúsculas) -> motor. Lo que usa la pasada 4 para ubicar."""
        merged = {**self.libraries, **self.db_schemas}
        return {name.upper(): engine for name, engine in merged.items()}


@dataclass(frozen=True)
class Project:
    placement_strategy: str = "flow"  # push_to_db o flow
    target_engine: str = "impala"
    reports: str = "discard"  # discard, log o csv
    max_components_per_job: int = 200


@dataclass(frozen=True)
class External:
    name: str  # nombre de archivo en minúsculas, sin ruta
    defines: tuple[str, ...] = ()  # variables de macro que el archivo define
    as_context: bool = True  # si las variables pasan a contexto del Job


@dataclass
class Env:
    engines: Engines = field(default_factory=Engines)
    project: Project = field(default_factory=Project)
    externals: dict[str, External] = field(default_factory=dict)  # nombre -> declaración
    external_files: dict[str, str] = field(default_factory=dict)  # "externals/x.sas" -> texto


def _object(data: Any, source: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError(f"{source}: debe ser un objeto JSON")
    return data


def _string_map(
    data: Any, source: str, field_name: str, pattern: re.Pattern[str]
) -> dict[str, str]:
    mapping = _object(data, f"{source}:{field_name}")
    out: dict[str, str] = {}
    for key, value in mapping.items():
        if not isinstance(value, str) or not pattern.match(value):
            raise ConfigError(f"{source}: {field_name}.{key} debe ser un nombre de motor válido")
        out[str(key)] = value
    return out


def parse_engines(data: Any, source: str = "engines.json") -> Engines:
    raw = _object(data, source)
    unknown = set(raw) - {"dsn", "libraries", "db_schemas"}
    if unknown:
        raise ConfigError(f"{source}: campos desconocidos {sorted(unknown)}")
    return Engines(
        dsn=_string_map(raw.get("dsn", {}), source, "dsn", _ENGINE),
        libraries=_string_map(raw.get("libraries", {}), source, "libraries", _ENGINE),
        db_schemas=_string_map(raw.get("db_schemas", {}), source, "db_schemas", _ENGINE),
    )


def parse_project(data: Any, source: str = "project.json") -> Project:
    raw = _object(data, source)
    known = {"placement_strategy", "target_engine", "reports", "max_components_per_job"}
    unknown = set(raw) - known
    if unknown:
        raise ConfigError(f"{source}: campos desconocidos {sorted(unknown)}")
    base = Project()
    strategy = raw.get("placement_strategy", base.placement_strategy)
    if strategy not in PLACEMENTS:
        raise ConfigError(f"{source}: placement_strategy debe ser uno de {sorted(PLACEMENTS)}")
    reports = raw.get("reports", base.reports)
    if reports not in REPORTS:
        raise ConfigError(f"{source}: reports debe ser uno de {sorted(REPORTS)}")
    engine = raw.get("target_engine", base.target_engine)
    if not isinstance(engine, str) or not _ENGINE.match(engine):
        raise ConfigError(f"{source}: target_engine debe ser un nombre de motor válido")
    maximum = raw.get("max_components_per_job", base.max_components_per_job)
    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
        raise ConfigError(f"{source}: max_components_per_job debe ser un entero mayor que 0")
    return Project(strategy, engine, reports, maximum)


def parse_externals(data: Any, source: str = "externals.json") -> dict[str, External]:
    raw = _object(data, source)
    declared: dict[str, External] = {}
    for file_name, spec in raw.items():
        if "/" in file_name or "\\" in file_name or not file_name:
            raise ConfigError(f"{source}: {file_name!r} debe ser solo el nombre del archivo")
        body = _object(spec, f"{source}:{file_name}")
        unknown = set(body) - {"defines", "as_context"}
        if unknown:
            raise ConfigError(f"{source}:{file_name}: campos desconocidos {sorted(unknown)}")
        defines = body.get("defines", [])
        if not isinstance(defines, list) or not all(
            isinstance(v, str) and _IDENTIFIER.match(v) for v in defines
        ):
            raise ConfigError(f"{source}:{file_name}: defines debe ser una lista de nombres")
        as_context = body.get("as_context", True)
        if not isinstance(as_context, bool):
            raise ConfigError(f"{source}:{file_name}: as_context debe ser true o false")
        key = file_name.lower()
        declared[key] = External(key, tuple(defines), as_context)
    return declared


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(
            f"{path.name}: JSON no válido ({error.msg}, línea {error.lineno})"
        ) from error


def load_env(root: Path = ENV_DIR) -> Env:
    """Carga y valida `env/`. Lo que falta usa sus valores por defecto."""
    env = Env()
    engines = _read_json(root / "engines.json")
    if engines is not None:
        env.engines = parse_engines(engines)
    project = _read_json(root / "project.json")
    if project is not None:
        env.project = parse_project(project)
    externals = _read_json(root / "externals.json")
    if externals is not None:
        env.externals = parse_externals(externals)
    folder = root / "externals"
    if folder.is_dir():
        for path in sorted(folder.glob("*.sas")):
            text = path.read_text(encoding="utf-8", errors="replace")
            env.external_files[f"externals/{path.name.lower()}"] = text
    return env
