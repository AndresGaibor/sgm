"""Salud de Talend Studio en una línea y menos de diez segundos.

Uso:
    uv run python tools/studio_salud.py --talend-dir CARPETA --proyecto RUTA
    uv run python tools/studio_salud.py --mcp [--url http://127.0.0.1:3927/mcp]

Sale con 0 si Studio responde y deja escribir; con 1 si no, y el motivo en la línea.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sgm.backend_talend import McpBackend, TalendCliBackend
from sgm.backend_talend.salud import comprobar_salud


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Comprueba que Talend Studio responde.")
    parser.add_argument("--talend-dir", type=Path, help="carpeta de talend-mcp (backend CLI)")
    parser.add_argument("--proyecto", type=Path, help="carpeta del proyecto Talend (backend CLI)")
    parser.add_argument("--mcp", action="store_true", help="usar el servidor MCP ya arrancado")
    parser.add_argument("--url", default=None, help="URL del MCP; por defecto TALEND_MCP_URL")
    parser.add_argument(
        "--tiempo-max", type=float, default=10.0, help="segundos de espera (10 por omisión)"
    )
    args = parser.parse_args(argv)

    if args.mcp:
        backend = McpBackend(url=args.url, tiempo_max=args.tiempo_max)
    else:
        if not args.talend_dir or not args.proyecto:
            parser.error("sin --mcp hacen falta --talend-dir y --proyecto")
        backend = TalendCliBackend(args.talend_dir, args.proyecto)
    salud = comprobar_salud(backend, args.tiempo_max)
    if salud.ok:
        print("Studio responde y deja escribir.")
        return 0
    print(f"Studio no está disponible: {salud.motivo}")
    return 1


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    raise SystemExit(main())
