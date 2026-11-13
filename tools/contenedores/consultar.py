"""Consulta filas del Impala local mediante un cliente de contenedor efímero."""

from __future__ import annotations

import csv
import io
import subprocess

RED = "sgmtest_impala_red"
CLIENTE = "apache/impala:4.5.3-impala_quickstart_client"
ANFITRION = "impalad:21050"


def filas_de_salida(texto: str) -> list[list[str]]:
    """Interpreta la salida CSV de `impala-shell -B` y omite líneas vacías."""
    return [fila for fila in csv.reader(io.StringIO(texto, newline="")) if fila]


def consultar(sql: str) -> list[list[str]]:
    """Ejecuta una consulta en la red del contenedor y devuelve las filas sin cabecera."""
    orden = [
        "docker",
        "run",
        "--rm",
        "--network",
        RED,
        "--entrypoint",
        "impala-shell",
        CLIENTE,
        "-i",
        ANFITRION,
        "-q",
        sql,
        "-B",
        "--output_delimiter=,",
    ]
    try:
        resultado = subprocess.run(orden, capture_output=True, text=True, check=False)
    except OSError as error:
        raise RuntimeError(
            f"No se pudo iniciar el cliente Impala del contenedor: {error}"
        ) from error
    if resultado.returncode != 0:
        detalle = resultado.stderr.strip() or resultado.stdout.strip()
        raise RuntimeError(detalle or "impala-shell terminó con error")
    return filas_de_salida(resultado.stdout)


__all__ = ["consultar", "filas_de_salida"]
