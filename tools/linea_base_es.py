"""Línea base de las construcciones de entrada y salida del migrador."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))

from corpus_lib.caso import todos_los_casos  # noqa: E402

CORPUS_POR_DEFECTO = RAIZ / "tests" / "corpus"
SALIDA_POR_DEFECTO = RAIZ / "out" / "linea_base_es.json"

_PATRONES: dict[str, re.Pattern[str]] = {
    "PROC IMPORT": re.compile(r"\bproc\s+import\b", re.IGNORECASE),
    "PROC EXPORT": re.compile(r"\bproc\s+export\b", re.IGNORECASE),
    "INFILE": re.compile(r"\binfile\b", re.IGNORECASE),
    "INPUT": re.compile(r"\binput\b", re.IGNORECASE),
    "FILE": re.compile(r"\bfile\b", re.IGNORECASE),
    "PUT": re.compile(r"\bput\b", re.IGNORECASE),
    "LIBNAME": re.compile(r"\blibname\b", re.IGNORECASE),
    "FILENAME": re.compile(r"\bfilename\b", re.IGNORECASE),
    "CONNECT TO": re.compile(r"\bconnect\s+to\b", re.IGNORECASE),
    "RSUBMIT": re.compile(r"\brsubmit\b", re.IGNORECASE),
    "PROC UPLOAD": re.compile(r"\bproc\s+upload\b", re.IGNORECASE),
    "PROC DOWNLOAD": re.compile(r"\bproc\s+download\b", re.IGNORECASE),
    "DBMS=XLSX": re.compile(r"\bdbms\s*=\s*xlsx\b", re.IGNORECASE),
    "DBMS=XLS": re.compile(r"\bdbms\s*=\s*xls\b", re.IGNORECASE),
    "GUESSINGROWS": re.compile(r"\bguessingrows\b", re.IGNORECASE),
    "INFORMAT": re.compile(r"\binformat\b", re.IGNORECASE),
    "FORMAT": re.compile(r"\bformat\b", re.IGNORECASE),
}
CONSTRUCCIONES_ES: tuple[str, ...] = tuple(_PATRONES)


def _pendientes(corpus: Path) -> dict[str, str]:
    ruta = corpus / "migrar_pendientes.yaml"
    if not ruta.is_file():
        return {}
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if datos is None:
        return {}
    if not isinstance(datos, dict) or any(
        not isinstance(nombre, str) or not isinstance(codigo, str)
        for nombre, codigo in datos.items()
    ):
        raise ValueError(f"{ruta}: se esperaba un mapa de caso a código de pendiente")
    return datos


def medir(corpus: Path, programas: Sequence[Path] = ()) -> dict:
    """Cuenta casos, códigos de pendiente y usos explícitos de cada construcción."""
    casos = todos_los_casos(corpus)
    pendientes = _pendientes(corpus)
    casos_por_construccion: Counter[str] = Counter()
    casos_por_nivel: dict[str, Counter[str]] = {}
    pendientes_por_construccion: dict[str, Counter[str]] = {
        nombre: Counter() for nombre in CONSTRUCCIONES_ES
    }

    for caso in casos:
        declaradas = "\n".join(caso.construcciones)
        encontradas = [
            nombre for nombre, patron in _PATRONES.items() if patron.search(declaradas)
        ]
        casos_por_construccion.update(encontradas)
        casos_por_nivel.setdefault(caso.nivel, Counter()).update(encontradas)
        codigo = pendientes.get(caso.nombre)
        if codigo:
            for nombre in encontradas:
                pendientes_por_construccion[nombre][codigo] += 1

    textos = [programa.read_text(encoding="utf-8", errors="replace") for programa in programas]
    return {
        "construcciones": {
            nombre: {
                "casos": casos_por_construccion[nombre],
                "pendientes": dict(sorted(pendientes_por_construccion[nombre].items())),
                "usos_programas": sum(
                    len(patron.findall(texto)) for texto in textos
                ),
            }
            for nombre, patron in _PATRONES.items()
        },
        "casos_por_nivel": {
            nivel: {nombre: contador[nombre] for nombre in CONSTRUCCIONES_ES}
            for nivel, contador in sorted(
                casos_por_nivel.items(), key=lambda item: int(item[0][1:])
            )
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", nargs="?", type=Path, default=CORPUS_POR_DEFECTO)
    parser.add_argument("--programa", action="append", type=Path, default=[])
    argumentos = parser.parse_args(argv)

    resultado = medir(argumentos.corpus, argumentos.programa)
    SALIDA_POR_DEFECTO.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_POR_DEFECTO.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    print(f"escrito: {SALIDA_POR_DEFECTO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
