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
from collections import Counter
from pathlib import Path

from corpus_semantica_funciones import FALTANTE, FUNCIONES, Faltante, cmp, evaluar

from sgm.migrar import semantica

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


def evaluar_vector(funcion: str, entrada: list) -> object:
    """Importa el intérprete solo al pedir ese motor y mantiene el oráculo independiente."""
    from sgm.migrar.interprete_vectores import evaluar_vector as evaluar_en_interprete

    return evaluar_en_interprete(funcion, entrada)


def _coincide_interprete(obtenido: object, esperado: object) -> bool:
    """El intérprete representa un faltante como `None` o como texto en blanco."""
    if esperado == "faltante":
        return isinstance(obtenido, Faltante) or semantica.es_faltante(obtenido)
    return _coincide(obtenido, esperado)


def _resultados_equivalentes(oraculo: object, interprete: object) -> bool:
    """Compara motores sin confundir faltantes ni booleanos con números."""
    falta_oraculo = isinstance(oraculo, Faltante) or semantica.es_faltante(oraculo)
    falta_interprete = isinstance(interprete, Faltante) or semantica.es_faltante(interprete)
    if falta_oraculo or falta_interprete:
        return falta_oraculo and falta_interprete
    if isinstance(oraculo, bool) or isinstance(interprete, bool):
        return type(oraculo) is bool and type(interprete) is bool and oraculo == interprete
    if isinstance(oraculo, (int, float)) and isinstance(interprete, (int, float)):
        return math.isclose(oraculo, interprete, rel_tol=0, abs_tol=1e-9)
    return oraculo == interprete


def verificar(ruta: Path = RUTA_VECTORES, motor: str = "oraculo") -> dict:
    """Ejecuta vectores en un motor y, para el intérprete, cruza también con el oráculo."""
    if motor not in ("oraculo", "interprete"):
        raise ValueError(f"motor no válido: {motor!r}")
    vectores = cargar_vectores(ruta)
    fallos, inciertos, diferencias_motores, pasan = [], [], [], 0
    por_confianza = dict.fromkeys(CONFIANZAS, 0)
    ejecuciones_por_funcion: Counter[str] = Counter()
    for vector in vectores:
        confianza = vector.get("confianza")
        if confianza not in CONFIANZAS:
            raise ValueError(f"confianza no válida en {vector.get('id')}: {confianza!r}")
        por_confianza[confianza] += 1
        if confianza == "incierto":
            inciertos.append(vector)
            continue
        funcion = str(vector["funcion"]).strip().lower()
        ejecuciones_por_funcion[funcion] += 1
        oraculo = ejecutar_vector(vector)
        if motor == "oraculo":
            obtenido = oraculo
            coincide = _coincide(obtenido, vector["esperado"])
        else:
            try:
                obtenido = evaluar_vector(vector["funcion"], vector["entrada"])
            except Exception as error:
                obtenido = error
                diferencias_motores.append(
                    {"id": vector["id"], "oraculo": repr(oraculo), "interprete": str(error)}
                )
                coincide = False
            else:
                coincide = _coincide_interprete(obtenido, vector["esperado"])
                if not _resultados_equivalentes(oraculo, obtenido):
                    diferencias_motores.append(
                        {
                            "id": vector["id"],
                            "oraculo": repr(oraculo),
                            "interprete": repr(obtenido),
                        }
                    )
        if coincide:
            pasan += 1
        else:
            fallo = {**vector, "obtenido": repr(obtenido)}
            if isinstance(obtenido, Exception):
                fallo["error"] = f"{type(obtenido).__name__}: {obtenido}"
            fallos.append(fallo)
    return {
        "motor": motor,
        "total": len(vectores),
        "por_confianza": por_confianza,
        "pasan": pasan,
        "fallos": fallos,
        "inciertos": inciertos,
        "ejecuciones_por_funcion": dict(sorted(ejecuciones_por_funcion.items())),
        "diferencias_motores": diferencias_motores,
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
        if "error" in f:
            print(f"    ERROR {f['error']}")
    if resultado["diferencias_motores"]:
        print(f"Diferencias oráculo/intérprete: {len(resultado['diferencias_motores'])}")
        for diferencia in resultado["diferencias_motores"]:
            print(
                f"  DIFERENCIA {diferencia['id']} oráculo={diferencia['oraculo']} "
                f"intérprete={diferencia['interprete']}"
            )
    total_ejecutados = sum(resultado["ejecuciones_por_funcion"].values())
    print(f"Ejecuciones en {resultado['motor']}: {total_ejecutados}")
    print(f"Inciertos (no cuentan como fallo): {len(resultado['inciertos'])}")
    for v in resultado["inciertos"]:
        print(f"  INCIERTO {v['id']} {v['funcion']}{v['entrada']}")


def main(argumentos: list[str] | None = None) -> int:
    """Punto de entrada de línea de comandos. Devuelve 1 si algún vector documentado falla."""
    parser = argparse.ArgumentParser(description="Verifica la semántica de funciones SAS.")
    sub = parser.add_subparsers(dest="comando", required=True)
    verif = sub.add_parser("verificar", help="ejecuta los vectores contra la implementación")
    verif.add_argument("--ruta", type=Path, default=RUTA_VECTORES)
    verif.add_argument("--motor", choices=("oraculo", "interprete"), default="oraculo")
    args = parser.parse_args(argumentos)
    resultado = verificar(args.ruta, motor=args.motor)
    _imprimir_reporte(resultado)
    return 1 if resultado["fallos"] or resultado["diferencias_motores"] else 0


if __name__ == "__main__":
    sys.exit(main())
