"""Un solo comando para cerrar un hito: `ruff`, suite, cruces del corpus y oráculo.

Uso:
    uv run python tools/ci.py              todo
    uv run python tools/ci.py --sin-suite  sin la suite completa (para iterar)
    uv run python tools/ci.py --sin-tablero  sin la fotografía del tablero

Pasos, en orden:
1. `ruff check .`
2. `pytest -q` — suite completa; es lo que corre el cierre de un hito de `AGENTS.md`.
3. Cruces del corpus: `pytest -q -n0 tests/unit/test_corpus_totales_cruce.py
   tests/unit/test_corpus_validaciones.py`. Van aparte de la suite para que un cruce roto se nombre
   en el informe y no se pierda entre 1 500 pruebas.
4. `tools/corpus.py oraculo todos --verificar`, que regenera el esperado de cada caso y lo compara.
5. Tablero (`tools/tablero.py`): informativo, no puede hacer fallar el cierre.

Al terminar deja el resultado en `.cache/validacion/` (`tools/validacion.py`): el gancho
`pre-commit` rechaza un commit si el árbol cambió desde este cierre o si algún paso obligatorio
quedó en rojo. `--sin-registro` existe solo para las pruebas del propio cierre.

Código de salida: 0 si todos los pasos obligatorios pasan; 1 si alguno falla; 2 si el uso no vale.
De cada paso fallido se imprime la cola de su salida, que es lo que hace falta para arreglarlo.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "tools") not in sys.path:
    sys.path.insert(0, str(REPO / "tools"))

import validacion  # noqa: E402

CRUCES = (
    "tests/unit/test_corpus_totales_cruce.py",
    "tests/unit/test_corpus_validaciones.py",
)
COLA = 25


@dataclass(frozen=True)
class Paso:
    """Un paso del cierre: nombre para el informe y comando que se ejecuta."""

    nombre: str
    comando: tuple[str, ...]
    obligatorio: bool = True


@dataclass(frozen=True)
class Resultado:
    """Lo que dejó un paso: si falló, cuánto tardó y la cola de su salida."""

    paso: Paso
    codigo: int
    segundos: float
    salida: str

    @property
    def ok(self) -> bool:
        return self.codigo == 0 or not self.paso.obligatorio

    @property
    def marca(self) -> str:
        if self.codigo == 0:
            return "OK"
        return "FALLA" if self.paso.obligatorio else "aviso"


def pasos(con_suite: bool, con_tablero: bool) -> list[Paso]:
    """Los pasos del cierre, en el orden en que se ejecutan."""
    python = sys.executable
    lista = [
        Paso("ruff", ("ruff", "check", ".")),
        Paso("cruces del corpus", (python, "-m", "pytest", "-q", "-n0", *CRUCES)),
        Paso("oráculo del corpus", (python, "tools/corpus.py", "oraculo", "todos", "--verificar")),
    ]
    if con_suite:
        lista.insert(1, Paso("suite", (python, "-m", "pytest", "-q")))
    if con_tablero:
        lista.append(Paso("tablero", (python, "tools/tablero.py", "--markdown"), obligatorio=False))
    return lista


def _comando(partes: tuple[str, ...]) -> list[str]:
    """`ruff` se resuelve en el PATH del entorno de uv; el resto ya viene con el python del venv."""
    if partes[0] == "ruff":
        return [str(Path(sys.executable).parent / "ruff"), *partes[1:]]
    return list(partes)


def ejecutar(paso: Paso) -> Resultado:
    """Corre el paso en la raíz del repositorio y guarda la cola de la salida combinada."""
    inicio = time.perf_counter()
    proceso = subprocess.run(
        _comando(paso.comando),
        cwd=REPO,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    segundos = time.perf_counter() - inicio
    lineas = [linea for linea in (proceso.stdout + proceso.stderr).splitlines() if linea.strip()]
    return Resultado(paso, proceso.returncode, segundos, "\n".join(lineas[-COLA:]))


def informe(resultados: list[Resultado]) -> str:
    """Tabla Markdown con el resultado de cada paso y la cifra que deja la suite."""
    lineas = ["", "| Paso | Resultado | Segundos |", "|---|---|---:|"]
    for resultado in resultados:
        lineas.append(
            f"| {resultado.paso.nombre} | {resultado.marca} | {resultado.segundos:.1f} |"
        )
    return "\n".join(lineas)


PASOS_DE_VALIDACION = {
    "ruff": "ruff",
    "suite": "pytest",
    "cruces del corpus": "cruces",
    "oráculo del corpus": "oraculo",
}


def _resumen(resultado: Resultado) -> str:
    """La última línea con contenido: en pytest es la cifra, en ruff el veredicto."""
    lineas = [linea for linea in resultado.salida.splitlines() if linea.strip()]
    return lineas[-1] if lineas else ""


def registrar_cierre(
    resultados: list[Resultado],
    *,
    con_suite: bool,
    base: Path | None = None,
    repo: Path = REPO,
    huella: str | None = None,
) -> dict:
    """Deja en `.cache/validacion/` lo que el gancho `pre-commit` va a exigir.

    Con `con_suite=False` no se escribe el paso `ci`: un cierre sin la suite completa no autoriza
    un commit. Los pasos que sí corrieron se anotan igual, para que `validacion.py estado` diga qué
    falta.
    """
    actual = huella or validacion.huella_arbol(repo)
    for resultado in resultados:
        paso = PASOS_DE_VALIDACION.get(resultado.paso.nombre)
        if paso is None:
            continue
        validacion.registrar(
            paso,
            resultado.codigo == 0,
            _resumen(resultado),
            repo=repo,
            base=base,
            huella=actual,
        )
    if not con_suite:
        return validacion.leer_estado(base)
    fallos = [
        resultado.paso.nombre
        for resultado in resultados
        if resultado.paso.obligatorio and resultado.codigo != 0
    ]
    resumen = "Todo verde" if not fallos else f"Falla: {', '.join(fallos)}"
    return validacion.registrar(
        "ci", not fallos, resumen, repo=repo, base=base, huella=actual
    )


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sin-suite", action="store_true", help="omite `pytest -q`")
    parser.add_argument("--sin-tablero", action="store_true", help="omite el tablero")
    parser.add_argument(
        "--sin-registro",
        action="store_true",
        help="no deja estado para el candado de commit (solo para pruebas)",
    )
    args = parser.parse_args(argv)
    resultados: list[Resultado] = []
    for paso in pasos(not args.sin_suite, not args.sin_tablero):
        print(f"[{paso.nombre}] {paso.comando[0]} ...", flush=True)
        resultado = ejecutar(paso)
        resultados.append(resultado)
        print(f"[{paso.nombre}] {resultado.marca} en {resultado.segundos:.1f} s")
        if resultado.codigo != 0 and paso.obligatorio:
            print(resultado.salida)
        elif paso.nombre == "tablero":
            print(resultado.salida)
        elif paso.nombre == "suite" and resultado.salida:
            print(resultado.salida.splitlines()[-1])
    print(informe(resultados))
    if not args.sin_registro:
        registrar_cierre(resultados, con_suite=not args.sin_suite)
    fallos = [r for r in resultados if not r.ok]
    if fallos:
        print(f"Falla: {', '.join(r.paso.nombre for r in fallos)}.", file=sys.stderr)
        return 1
    print("Todo verde.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
