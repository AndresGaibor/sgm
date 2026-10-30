"""Almacén SQLite de decisiones (overrides) e inventario de huecos.

Vive en `~/.sgm/sgm.sqlite`; la variable `SGM_DB` lo cambia. Usa `sqlite3` de la librería estándar.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS overrides (
    signature TEXT NOT NULL,
    scope TEXT NOT NULL,
    ref TEXT NOT NULL DEFAULT '',
    option TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    date TEXT NOT NULL,
    PRIMARY KEY (signature, scope, ref)
);
CREATE TABLE IF NOT EXISTS gaps (
    signature TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    files TEXT NOT NULL,
    occurrences INTEGER NOT NULL,
    example TEXT NOT NULL
);
"""


def default_path() -> Path:
    return Path(os.environ.get("SGM_DB", Path.home() / ".sgm" / "sgm.sqlite"))


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
