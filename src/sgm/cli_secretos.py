"""Comando `sgm secretos`: compuerta de secretos sobre artefactos, antes de un despliegue (R4-05).

Sale con código 1 si hay hallazgos y con 0 si no. Nunca imprime el valor sospechoso completo: cada
hallazgo muestra los 2 primeros caracteres y `***`. Va aparte de `sgm.cli` para no pasar el límite
de 300 líneas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sgm.seguridad.escaner_secretos import Escaneo, escanear_ruta

FORMATOS = ("texto", "json")


def _texto(escaneo: Escaneo) -> str:
    lineas = [f"{h.archivo}:{h.linea}: {h.tipo}: {h.valor}" for h in escaneo.hallazgos]
    archivos = len({h.archivo for h in escaneo.hallazgos})
    lineas.append(
        f"{len(escaneo.hallazgos)} hallazgo(s) en {archivos} archivo(s); "
        f"{escaneo.revisados} archivo(s) revisado(s)"
    )
    return "\n".join(lineas)


def _json(escaneo: Escaneo) -> str:
    payload = {
        "revisados": escaneo.revisados,
        "hallazgos": [
            {"archivo": h.archivo, "linea": h.linea, "tipo": h.tipo, "valor": h.valor}
            for h in escaneo.hallazgos
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def secretos_command(
    ruta: Annotated[Path, typer.Argument(help="Carpeta o archivo que se revisa.")],
    formato: Annotated[str, typer.Option("--formato", help="texto o json.")] = "texto",
) -> None:
    """Busca contraseñas, tokens y claves en claro. Sale con 1 si hay hallazgos, con 0 si no."""
    if not ruta.exists():
        raise typer.BadParameter(f"no existe: {ruta}")
    if formato not in FORMATOS:
        raise typer.BadParameter(f"formato desconocido {formato!r}; use texto o json")
    escaneo = escanear_ruta(ruta)
    typer.echo(_json(escaneo) if formato == "json" else _texto(escaneo))
    if escaneo.hallazgos:
        raise typer.Exit(code=1)
