"""Caché por contenido para las pruebas. Vive en `.test-cache/` (raíz del repo, ignorada por git).

Clave de cada entrada = sha256 de: la versión de este módulo, el hash de todo el código que decide el
resultado (`src/sas_grid_migrator`, `apps/api`, `rules`, `contract`, `schemas`) y las entradas propias de
cada prueba (contenido del SAS, opciones, fixtures). Si algo de eso cambia, la clave cambia y se recalcula:
nunca se sirve un dato viejo. Borrar la carpeta es siempre seguro (`scripts/test.ps1 -Clean`).

Con xdist: la escritura es atómica (archivo temporal + `os.replace`) y un lock por clave evita que varios
workers recalculen lo mismo a la vez. El primero calcula y guarda; los demás esperan y leen.

`SGM_TEST_CACHE=0` desactiva la caché (recalcula todo y no guarda nada).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / ".test-cache"
#: Súbela si cambia el formato de lo que se guarda o la forma de calcular la clave.
CACHE_VERSION = "1"
#: Un lock más viejo que esto se considera abandonado (worker muerto a la fuerza).
STALE_LOCK_SECONDS = 900

#: Código y reglas que determinan cualquier resultado de planificación, preview o catálogo.
CODE_GLOBS = [
    ("src/sas_grid_migrator", "*.py"),
    ("apps/api", "*.py"),
    ("rules", "*.json"),
    ("contract", "*.json"),
    ("schemas", "*.json"),
]
MCP_GLOBS = [
    ("mcp/talend-mcp/src", "*.ts"),
    ("mcp/talend-mcp", "package.json"),
    ("mcp/talend-mcp", "index.ts"),
]


def cache_enabled() -> bool:
    return os.environ.get("SGM_TEST_CACHE", "1") != "0"


def _files(globs: list[tuple[str, str]]) -> list[Path]:
    found: list[Path] = []
    for base, pattern in globs:
        found.extend(p for p in (REPO / base).rglob(pattern) if p.is_file() and "__pycache__" not in p.parts)
    return sorted(set(found))


def _digest(paths: list[Path], root: Path | None = None) -> str:
    root = root or REPO  # en tiempo de ejecución: así un REPO redefinido (tests del propio helper) también vale
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@lru_cache(maxsize=1)
def code_fingerprint() -> str:
    """Hash de todo el código y las reglas que puede cambiar un resultado. Se calcula una vez por proceso."""
    return _digest(_files(CODE_GLOBS))


@lru_cache(maxsize=1)
def mcp_fingerprint() -> str:
    """Hash del código del MCP real (para cachear lo que publica sin arrancarlo)."""
    return _digest(_files(MCP_GLOBS))


def tree_fingerprint(path: Path) -> str:
    """Hash de un archivo o de un árbol de archivos (nombres relativos y contenido)."""
    if path.is_file():
        return _digest([path], root=path.parent)
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return _digest(files, root=path)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=str)
    if isinstance(value, Path):
        return value.as_posix()
    return str(value)


def _read(target: Path) -> Any | None:
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_atomic(target: Path, value: Any) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False)
    for _ in range(20):
        try:
            os.replace(tmp, target)
            return
        except PermissionError:  # Windows: otro proceso está leyendo el destino; reintenta.
            time.sleep(0.1)
    Path(tmp).unlink(missing_ok=True)


def _try_lock(lock: Path) -> bool:
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        return False


def cached_json(namespace: str, payload: Any, compute: Callable[[], Any]) -> Any:
    """Devuelve `compute()` desde disco si la clave (namespace + payload + código) ya existe.

    `compute` debe devolver algo serializable en JSON. El valor que se devuelve siempre es el que se lee
    del disco o el que acaba de calcularse, así que la forma es la misma en frío y en caliente.
    """
    if not cache_enabled():
        return compute()
    text = json.dumps([CACHE_VERSION, code_fingerprint(), namespace, payload], sort_keys=True, default=_jsonable)
    target = CACHE_ROOT / namespace / f"{hashlib.sha256(text.encode('utf-8')).hexdigest()}.json"
    lock = target.with_suffix(".lock")
    target.parent.mkdir(parents=True, exist_ok=True)
    while True:
        hit = _read(target)
        if hit is not None:
            return hit
        if _try_lock(lock):
            try:
                hit = _read(target)  # otro worker pudo terminar justo antes de que obtuviéramos el lock
                if hit is not None:
                    return hit
                value = compute()
                _write_atomic(target, value)
                return value
            finally:
                lock.unlink(missing_ok=True)
        try:
            if time.time() - lock.stat().st_mtime > STALE_LOCK_SECONDS:
                lock.unlink(missing_ok=True)
                continue
        except FileNotFoundError:
            continue
        time.sleep(0.2)


def _source_fingerprint(source: Path | str) -> dict[str, str]:
    """Identidad de lo que se planifica: un SAS en texto, un archivo, o una carpeta entera."""
    if isinstance(source, str):
        return {"text": hashlib.sha256(source.encode("utf-8")).hexdigest()}
    return {"tree": tree_fingerprint(source)}


def cached_planset(source: Path | str, *, settings: dict[str, Any] | None = None, **plan_options: Any):
    """`PlanSet` de un SAS (texto), de un archivo o de una carpeta, desde la caché de disco.

    Cada llamada usa un proyecto temporal nuevo; el resultado se devuelve como `PlanSet` validado
    (la misma forma en frío y en caliente). `settings` son los campos de `Settings` (p. ej.
    `report_policy`) y `plan_options` los de `generate_plans` (p. ej. `fresh`).
    """
    from sas_grid_migrator.config import Settings
    from sas_grid_migrator.migration_planner.models import PlanSet
    from sas_grid_migrator.migration_planner.service import generate_plans
    from sas_grid_migrator.persistence.store import Store

    settings = dict(settings or {})

    def compute() -> dict:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            if isinstance(source, str):
                src = root / "src"
                src.mkdir()
                (src / "programa.sas").write_text(source, encoding="utf-8")
            elif source.is_file():
                src = root / "src"
                src.mkdir()
                shutil.copy(source, src / source.name)
            else:
                src = source
            store = Store(Settings(data_dir=root / "data", **settings))
            project = store.create_project("cache")
            store.import_batch(project.id, src)
            return generate_plans(store, project.id, **plan_options).model_dump(mode="json")

    payload = {"source": _source_fingerprint(source), "settings": settings, "plan": plan_options}
    return PlanSet.model_validate(cached_json("plans", payload, compute))
