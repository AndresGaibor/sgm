# PROGRESS

## Hito 0. Repositorio nuevo

- Fecha: 2026-10-30
- Qué se hizo: repositorio `git init` en `main`, paquete `uv init` con Python 3.12, estructura de carpetas, `pyproject.toml` (dependencias `networkx`, `typer`, `pyyaml`; dev `pytest`, `pytest-xdist`, `ruff`; `line-length = 100`; `addopts = -n auto`), `AGENTS.md`, `.gitignore`.
- Pruebas: 1 pasa (`test_el_paquete_importa`). `ruff check .` limpio.
- Bloqueos abiertos: ninguno.

## Decisiones

- El script de consola apunta a `sgm.cli:app` (Typer), tal como pide el prompt.
- Pydantic no se usa en el hito 0. Los modelos serán `dataclass`.
