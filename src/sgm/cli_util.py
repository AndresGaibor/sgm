"""Auxiliares de la CLI compartidos por sus módulos: lectura de programas y `env/`."""

from __future__ import annotations

from pathlib import Path

import typer

from sgm.catalog.config import ConfigError, Env, load_env
from sgm.ingest.importer import looks_like_sas


def _collect(path: Path) -> dict[str, str]:
    """Textos de los programas SAS: un archivo, o todos los de una carpeta (rutas relativas)."""
    if path.is_file():
        return {path.name: path.read_text(encoding="utf-8", errors="replace")}
    files: dict[str, str] = {}
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file() or candidate.suffix.lower() not in {".sas", ".txt"}:
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if candidate.suffix.lower() == ".sas" or looks_like_sas(text):
            files[candidate.relative_to(path).as_posix()] = text
    return files


def _env() -> Env:
    """`env/` cargado y validado. Un archivo mal formado detiene el comando con su mensaje."""
    try:
        return load_env()
    except ConfigError as error:
        typer.echo(f"Configuración no válida: {error}", err=True)
        raise typer.Exit(code=2) from error
