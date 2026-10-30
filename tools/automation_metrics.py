"""Métricas de automatización: envoltorio de `sgm metrics` para ejecutarlo sin instalar el script.

Uso: uv run python tools/automation_metrics.py <carpeta> [--out out]
"""

from __future__ import annotations

import sys

from typer.testing import CliRunner

from sgm.cli import app


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    result = CliRunner().invoke(app, ["metrics", *argv])
    print(result.output, end="")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
