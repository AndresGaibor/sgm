"""Ciclo rápido de desarrollo: lint, pruebas y oráculo de los casos tocados, en ese orden.

Se apoya en lo que ya cambió (`git diff --name-only HEAD`) para no correr el oráculo de 45 casos
cuando el cambio no toca ninguno. El primer comando que falla corta el ciclo y su código es el que
sale: no se sigue probando sobre una base que ya está mal.

Uso:
    uv run python tools/ciclo_rapido.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

Ejecutor = Callable[[list[str]], int]

CORPUS = "tests/corpus"


def _ruta_de_caso(archivo: str) -> str | None:
    """Directorio del caso del corpus al que pertenece un archivo, o None si no es del corpus."""
    partes = Path(archivo).as_posix().split("/")
    if len(partes) < 4 or "/".join(partes[:2]) != CORPUS:
        return None
    carpeta = Path("/".join(partes[:-1]))
    # Los casos de L8 viven en `L8/<grupo>/<caso>/`; el caso es la carpeta con `caso.yaml`.
    if (carpeta / "caso.yaml").is_file():
        return carpeta.as_posix()
    return "/".join(partes[:4])


def casos_tocados(archivos: list[str]) -> list[str]:
    """Directorios de caso del corpus que contienen alguno de los archivos, sin repetir."""
    encontrados = {caso for caso in map(_ruta_de_caso, archivos) if caso}
    return sorted(encontrados)


def comandos(archivos: list[str]) -> list[list[str]]:
    """Comandos del ciclo, en orden: lint de lo tocado, pruebas y oráculo de los casos."""
    lista: list[list[str]] = []
    python = [archivo for archivo in archivos if archivo.endswith(".py")]
    if python:
        lista.append(["uv", "run", "ruff", "check", *python])
    pruebas = [
        archivo
        for archivo in archivos
        if archivo.startswith("tests/") and archivo.endswith(".py")
    ]
    lista.append(["uv", "run", "pytest", "-q", "-n", "auto", "-m", "not studio", *pruebas])
    for caso in casos_tocados(archivos):
        lista.append(["uv", "run", "python", "tools/corpus.py", "oraculo", caso, "--verificar"])
    return lista


def archivos_cambiados() -> list[str]:
    """Archivos cambiados frente a HEAD, según `git diff --name-only HEAD`."""
    resultado = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, check=False
    )
    return [linea.strip() for linea in resultado.stdout.splitlines() if linea.strip()]


def _ejecutar(comando: list[str]) -> int:
    return subprocess.run(comando, check=False).returncode


def main(
    argv: list[str] | None = None,
    *,
    archivos: list[str] | None = None,
    ejecutar: Ejecutor | None = None,
    salida: Callable[[str], None] = print,
) -> int:
    """Corre el ciclo y sale con el primer código distinto de cero."""
    archivos = archivos_cambiados() if archivos is None else archivos
    ejecutar = ejecutar or _ejecutar
    for comando in comandos(archivos):
        inicio = time.perf_counter()
        codigo = ejecutar(comando)
        segundos = time.perf_counter() - inicio
        nombre = comando[2] if len(comando) > 2 else comando[0]
        salida(f"{nombre}: {segundos:.1f} s (código {codigo})")
        if codigo != 0:
            salida(f"corta en: {' '.join(comando)}")
            return codigo
    return 0


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
