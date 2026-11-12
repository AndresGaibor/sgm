"""Instala el gancho `pre-commit` versionado en `.githooks/`.

Uso:
    uv run python tools/instalar_ganchos.py

`core.hooksPath` es configuración local de Git: se hace una vez por copia del repositorio y no se
versiona. El gancho sí se versiona en `.githooks/pre-commit`; este comando solo lo activa y, en
Linux o macOS, le da permiso de ejecución.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GANCHO = Path(".githooks") / "pre-commit"


def instalar(repo: Path = REPO, *, salida=print) -> int:
    """Apunta `core.hooksPath` a `.githooks` y comprueba que el gancho exista."""
    if not (repo / GANCHO).is_file():
        print(f"Falta el gancho {repo / GANCHO}.", file=sys.stderr)
        return 1
    proceso = subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proceso.returncode != 0:
        print(
            f"No se pudo configurar core.hooksPath: {proceso.stderr.strip()}",
            file=sys.stderr,
        )
        return 1
    if os.name != "nt":
        (repo / GANCHO).chmod(0o755)
    salida("Gancho instalado: core.hooksPath=.githooks")
    salida("Estado del candado: uv run python tools/validacion.py estado")
    return 0


if __name__ == "__main__":
    raise SystemExit(instalar())
