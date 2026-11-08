"""Compuerta de liberación: un comando decide si la versión se puede publicar (MG-P14-02).

Pasos, en orden:

1. `ruff check .`
2. La suite completa (`pytest -q -n 4`); incluye los anillos A y B del corpus.
3. El oráculo del corpus: regenera el esperado de cada caso y lo compara.
4. Anillo D: `sgm migrar` dos veces sobre un caso del corpus; mismos archivos y mismos bytes.
5. `sgm secretos` sobre esa salida: cero hallazgos.
6. Versión: `pyproject.toml`, paquete instalado y `CHANGELOG.md` coinciden.

Sale con 0 solo si todos los pasos pasan. `--sin-suite` sirve para iterar sin esperar la suite.

Uso:
    uv run python tools/liberacion.py
    uv run python tools/liberacion.py --sin-suite
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MUESTRA = REPO / "tests" / "corpus" / "L2" / "l2_01_inner_join_clientes_ventas" / "programa.sas"
COLA = 20


@dataclass(frozen=True)
class Resultado:
    """Lo que dejó un paso: nombre, código, segundos y su detalle o la cola de su salida."""

    nombre: str
    codigo: int
    segundos: float
    detalle: str = ""

    @property
    def marca(self) -> str:
        return "OK" if self.codigo == 0 else "FALLA"


def _python() -> str:
    return sys.executable


def _comando_ruff() -> str:
    return str(Path(sys.executable).parent / "ruff")


def _cola(texto: str) -> str:
    lineas = [linea for linea in texto.splitlines() if linea.strip()]
    return "\n".join(lineas[-COLA:])


def _subproceso(nombre: str, comando: tuple[str, ...]) -> Resultado:
    """Corre un comando en la raíz del repositorio y guarda la cola de su salida."""
    inicio = time.perf_counter()
    proceso = subprocess.run(
        comando,
        cwd=REPO,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    segundos = time.perf_counter() - inicio
    return Resultado(nombre, proceso.returncode, segundos, _cola(proceso.stdout + proceso.stderr))


def _en_proceso(nombre: str, funcion: Callable[[], str]) -> Resultado:
    """Corre un paso en el mismo intérprete y convierte cualquier error en un fallo del informe."""
    inicio = time.perf_counter()
    try:
        detalle = funcion()
    except Exception as error:  # noqa: BLE001 — la compuerta informa el fallo, no lo esconde
        detalle = f"{type(error).__name__}: {error}"
        return Resultado(nombre, 1, time.perf_counter() - inicio, detalle)
    return Resultado(nombre, 0, time.perf_counter() - inicio, detalle)


def _version() -> str:
    """Comprueba que la versión tiene una sola fuente y que el changelog la nombra."""
    from sgm import __version__

    datos = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    declarada = str(datos["project"]["version"])
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    problemas: list[str] = []
    if __version__ != declarada:
        problemas.append(f"el paquete dice {__version__} y pyproject {declarada}")
    if f"## [{declarada}]" not in changelog:
        problemas.append(f"CHANGELOG.md no tiene la sección {declarada}")
    if "## [Sin publicar]" not in changelog:
        problemas.append("CHANGELOG.md no tiene la sección Sin publicar")
    if problemas:
        raise AssertionError("; ".join(problemas))
    return f"{declarada} en pyproject, paquete y changelog"


def _bytes(carpeta: Path) -> dict[str, bytes]:
    """Contenido de cada archivo de la carpeta, indexado por su ruta relativa."""
    return {
        archivo.relative_to(carpeta).as_posix(): archivo.read_bytes()
        for archivo in sorted(carpeta.rglob("*"))
        if archivo.is_file()
    }


def _salida() -> str:
    """Anillo D: dos migraciones iguales byte a byte, sin secretos en la salida."""
    from sgm.cli_migrar import migrar
    from sgm.seguridad.escaner_secretos import escanear_ruta

    if not MUESTRA.is_file():
        raise AssertionError(f"no existe el caso de la compuerta: {MUESTRA}")
    with tempfile.TemporaryDirectory(prefix="sgm-liberacion-") as temporal:
        uno = migrar(MUESTRA, Path(temporal) / "uno")
        dos = migrar(MUESTRA, Path(temporal) / "dos")
        arbol_uno = _bytes(uno.carpeta)
        arbol_dos = _bytes(dos.carpeta)
        if not arbol_uno:
            raise AssertionError("la migración no escribió ningún archivo")
        if arbol_uno != arbol_dos:
            claves = set(arbol_uno) ^ set(arbol_dos)
            claves |= {clave for clave in arbol_uno if arbol_uno[clave] != arbol_dos.get(clave)}
            distintos = ", ".join(sorted(claves)[:10])
            raise AssertionError(f"dos corridas dieron bytes distintos: {distintos}")
        escaneo = escanear_ruta(uno.carpeta)
        if escaneo.hallazgos:
            hallazgos = ", ".join(f"{h.archivo}:{h.linea}:{h.tipo}" for h in escaneo.hallazgos)
            raise AssertionError(f"la salida trae secretos: {hallazgos}")
        return f"{len(arbol_uno)} archivos; {escaneo.revisados} revisados, 0 hallazgos"


def _pasos(sin_suite: bool) -> list[tuple[str, str | Callable[[], str]]]:
    """Los pasos de la compuerta, en orden: nombre y comando lógico o función."""
    lista: list[tuple[str, str | Callable[[], str]]] = [
        ("ruff", "ruff"),
        ("oráculo del corpus", "oraculo"),
        ("determinismo y secretos", _salida),
        ("versión", _version),
    ]
    if not sin_suite:
        lista.insert(1, ("suite", "suite"))
    return lista


def _ejecutar(nombre: str, paso: str | Callable[[], str]) -> Resultado:
    if callable(paso):
        return _en_proceso(nombre, paso)
    if paso == "ruff":
        return _subproceso(nombre, (_comando_ruff(), "check", "."))
    if paso == "suite":
        # Cuatro workers: con `-n auto` esta máquina agota recursos y algunos workers no importan.
        return _subproceso(nombre, (_python(), "-m", "pytest", "-q", "-n", "4"))
    if paso == "oraculo":
        comando = (_python(), "tools/corpus.py", "oraculo", "todos", "--verificar")
        return _subproceso(nombre, comando)
    raise ValueError(f"paso desconocido: {paso!r}")


def _informe(resultados: list[Resultado]) -> str:
    lineas = ["", "| Paso | Resultado | Segundos | Detalle |", "|---|---|---:|---|"]
    for resultado in resultados:
        detalle = resultado.detalle.splitlines()[-1] if resultado.detalle else ""
        lineas.append(
            f"| {resultado.nombre} | {resultado.marca} | {resultado.segundos:.1f} | {detalle} |"
        )
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sin-suite", action="store_true", help="omite `pytest -q -n 4`")
    args = parser.parse_args(argv)
    resultados: list[Resultado] = []
    for nombre, paso in _pasos(args.sin_suite):
        print(f"[{nombre}] ...", flush=True)
        resultado = _ejecutar(nombre, paso)
        resultados.append(resultado)
        print(f"[{nombre}] {resultado.marca} en {resultado.segundos:.1f} s", flush=True)
        if resultado.codigo != 0:
            print(resultado.detalle)
    print(_informe(resultados))
    fallos = [resultado for resultado in resultados if resultado.codigo != 0]
    if fallos:
        print(f"No se libera: falla {', '.join(r.nombre for r in fallos)}.", file=sys.stderr)
        return 1
    print("Compuerta verde: la versión se puede publicar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
