"""CLI de sgm."""

import typer

app = typer.Typer(help="sgm: compila programas SAS a guías de migración Talend.")


@app.callback()
def main() -> None:
    """Punto de entrada de la CLI."""
