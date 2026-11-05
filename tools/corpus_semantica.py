"""Verificación de la semántica de funciones SAS contra los vectores de la capa B.

Las funciones están en `corpus_semantica_funciones.py`. Este módulo lee los vectores de
`tests/corpus/semantica/vectores.yaml`, los ejecuta y reporta los que fallan.
Los vectores `incierto` se reportan aparte y no cuentan como fallo.

Uso:
    uv run python tools/corpus_semantica.py verificar
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from corpus_semantica_funciones import FALTANTE, FUNCIONES, Faltante, cmp, evaluar

__all__ = ["FALTANTE", "FUNCIONES", "Faltante", "cmp", "evaluar"]

REPO = Path(__file__).resolve().parents[1]
RUTA_VECTORES = REPO / "tests" / "corpus" / "semantica" / "vectores.yaml"
CONFIANZAS = ("documentado", "deducido", "incierto")


def cargar_vectores(ruta: Path = RUTA_VECTORES) -> list[dict]:
    """Lee el subconjunto de YAML de `vectores.yaml`: una lista de mapas de valores JSON."""
    vectores: list[dict] = []
    actual: dict | None = None
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#") or limpia == "vectores:":
            continue
        inicio = re.match(r"^\s*-\s+(\w+):\s*(.*)$", linea)
        if inicio:
            actual = {}
            vectores.append(actual)
            actual[inicio.group(1)] = _valor(inicio.group(2))
            continue
        campo = re.match(r"^\s+(\w+):\s*(.*)$", linea)
        if not campo or actual is None:
            raise ValueError(f"línea no válida en {ruta}: {linea!r}")
        actual[campo.group(1)] = _valor(campo.group(2))
    return vectores


def _valor(bruto: str) -> object:
    """Un valor JSON si lo es; si no, la palabra tal cual (por ejemplo `faltante`)."""
    try:
        return json.loads(bruto)
    except json.JSONDecodeError:
        return bruto


def _coincide(obtenido: object, esperado: object) -> bool:
    """Compara el resultado de la función con el valor documentado."""
    if esperado == "faltante":
        return isinstance(obtenido, Faltante)
    if isinstance(obtenido, Faltante):
        return False
    if isinstance(esperado, bool) or isinstance(obtenido, bool):
        return type(obtenido) is bool and obtenido == esperado
    if isinstance(esperado, (int, float)) and isinstance(obtenido, (int, float)):
        return math.isclose(obtenido, esperado, rel_tol=0, abs_tol=1e-9)
    return obtenido == esperado


def ejecutar_vector(vector: dict) -> object:
    """Ejecuta un vector; los argumentos de `cmp` y de `input` llegan tal cual del YAML."""
    return evaluar(vector["funcion"], *vector["entrada"])


def verificar(ruta: Path = RUTA_VECTORES) -> dict:
    """Ejecuta todos los vectores. Los `incierto` se reportan aparte y no cuentan como fallo."""
    vectores = cargar_vectores(ruta)
    fallos, inciertos, pasan = [], [], 0
    por_confianza = dict.fromkeys(CONFIANZAS, 0)
    for vector in vectores:
        confianza = vector.get("confianza")
        if confianza not in CONFIANZAS:
            raise ValueError(f"confianza no válida en {vector.get('id')}: {confianza!r}")
        por_confianza[confianza] += 1
        if confianza == "incierto":
            inciertos.append(vector)
            continue
        obtenido = ejecutar_vector(vector)
        if _coincide(obtenido, vector["esperado"]):
            pasan += 1
        else:
            fallos.append({**vector, "obtenido": repr(obtenido)})
    return {
        "total": len(vectores),
        "por_confianza": por_confianza,
        "pasan": pasan,
        "fallos": fallos,
        "inciertos": inciertos,
    }


def _imprimir_reporte(resultado: dict) -> None:
    """Escribe el resumen de `verificar` en la salida estándar."""
    conteo = resultado["por_confianza"]
    print(f"Vectores: {resultado['total']}")
    print("Por confianza: " + ", ".join(f"{k}={conteo[k]}" for k in CONFIANZAS))
    print(f"Pasan: {resultado['pasan']}")
    print(f"Fallos: {len(resultado['fallos'])}")
    for f in resultado["fallos"]:
        print(f"  FALLA {f['id']} {f['funcion']}{f['entrada']} esperado={f['esperado']!r} "
              f"obtenido={f['obtenido']}")
    print(f"Inciertos (no cuentan como fallo): {len(resultado['inciertos'])}")
    for v in resultado["inciertos"]:
        print(f"  INCIERTO {v['id']} {v['funcion']}{v['entrada']}")


def main(argumentos: list[str] | None = None) -> int:
    """Punto de entrada de línea de comandos. Devuelve 1 si algún vector documentado falla."""
    parser = argparse.ArgumentParser(description="Verifica la semántica de funciones SAS.")
    sub = parser.add_subparsers(dest="comando", required=True)
    verif = sub.add_parser("verificar", help="ejecuta los vectores contra la implementación")
    verif.add_argument("--ruta", type=Path, default=RUTA_VECTORES)
    args = parser.parse_args(argumentos)
    resultado = verificar(args.ruta)
    _imprimir_reporte(resultado)
    return 1 if resultado["fallos"] else 0


if __name__ == "__main__":
    sys.exit(main())
