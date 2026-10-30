"""Caché de salidas en `out/.cache/`.

La clave es el hash de los textos de entrada y el de las reglas. Si nada cambió (ni un fuente, ni
`rules/`, ni `env/schemas/`, ni la versión de sgm), la salida guardada se copia tal cual.
La caché es por proyecto: un cambio en cualquier archivo invalida todo, porque las macros se
comparten entre archivos.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from sgm import __version__
from sgm.compile import ROOT_DIR, RULES_DIR

ENV_DIR = ROOT_DIR / "env"


def rules_hash() -> str:
    """Huella de todo lo que cambia una salida además del código fuente: `rules/` y `env/`.

    `env/` incluye los esquemas, los externos y la configuración del proyecto.
    """
    digest = hashlib.sha256(__version__.encode("utf-8"))
    for path in sorted(RULES_DIR.rglob("*")) + sorted(ENV_DIR.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(ROOT_DIR).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def project_key(files: dict[str, str]) -> str:
    digest = hashlib.sha256(rules_hash().encode("utf-8"))
    for name in sorted(files):
        digest.update(name.encode("utf-8") + b"\0" + files[name].encode("utf-8") + b"\0")
    return digest.hexdigest()[:24]


def cache_dir(out: Path, key: str) -> Path:
    return out / ".cache" / key


def restore(out: Path, key: str) -> list[str]:
    """Copia la salida guardada a `out`. Devuelve los nombres copiados; lista vacía si no hay
    caché."""
    source = cache_dir(out, key)
    if not source.is_dir():
        return []
    copied = []
    for path in sorted(source.iterdir()):
        if path.is_file():
            shutil.copy2(path, out / path.name)
            copied.append(path.name)
    return copied


def save(out: Path, key: str, names: list[str]) -> None:
    """Guarda en la caché los archivos ya escritos en `out`."""
    target = cache_dir(out, key)
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copy2(out / name, target / name)
