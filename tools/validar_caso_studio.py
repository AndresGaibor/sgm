"""Valida casos del corpus en Studio de punta a punta con un solo comando.

Uso:
    uv run python tools/validar_caso_studio.py <caso> [<caso> ...]

Para cada caso: migra el programa con las cabeceras de `entradas/` como muestra, deduce el mapa de
contexto (cada variable `ruta_<x>` apunta a la entrada o a la salida del mismo nombre) y corre
`corpus_studio.py validar`. Imprime el resultado literal del arnés y sale con 1 si algún caso falla.
No guarda nada en el repositorio: la salida va a una carpeta temporal.

Entorno (valores por omisión de este equipo, cambiables):
    TALEND_PROJECT   proyecto con `talend.project`
    TALEND_JAVA_BIN  carpeta `bin` del JDK de Studio
    TALEND_M2        caché `.m2/repository` de Studio
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
_TALEND = Path("C:/Talend/8.0.1")
_PROYECTO = _TALEND / "studio/workspace3/talendbancolombia-963626413/PRJ_BANCOLOMBIA"
_JAVA = _TALEND / "zulu21.50.19-ca-jdk21.0.11-win_x64/bin"
_M2 = _TALEND / "studio/configuration/.m2/repository"


def mapa_de_contexto(
    variables: list[str], entradas: list[str], salidas: list[str]
) -> dict[str, str]:
    """Variable `ruta_<x>` a archivo del caso: entrada con el mismo nombre o salida esperada."""
    por_nombre = {Path(e).stem.lower(): e for e in entradas}
    por_salida = {s.lower(): s for s in salidas}
    mapa: dict[str, str] = {}
    for variable in variables:
        nombre = variable.removeprefix("ruta_").lower()
        if nombre in por_nombre:
            mapa[variable] = f"entradas/{por_nombre[nombre]}"
        elif nombre in por_salida:
            mapa[variable] = f"salida/{por_salida[nombre]}.csv"
        else:
            raise ValueError(f"sin entrada ni salida conocida para la variable {variable}")
    return mapa


def _caso(nombre: str) -> Path:
    encontrados = sorted((RAIZ / "tests" / "corpus").glob(f"*/{nombre}"))
    if not encontrados:
        raise SystemExit(f"no existe el caso {nombre}")
    return encontrados[0]


def _correr(argumentos: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *argumentos], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8"
    )


def validar(nombre: str, sufijo: str) -> bool:
    carpeta = _caso(nombre)
    trabajo = Path(tempfile.mkdtemp(prefix=f"h-{nombre[:8]}-"))
    migra = _correr(
        ["-m", "sgm.cli", "migrar", str(carpeta / "programa.sas"), "--out", str(trabajo),
         "--muestra", str(carpeta / "entradas")]
    )
    paquete = trabajo / "programa"
    if migra.returncode != 0 or not (paquete / "process").is_dir():
        print(f"{nombre}: la migración no produjo Jobs\n{migra.stdout}{migra.stderr}")
        return False
    contexto = yaml.safe_load((paquete / "contextos" / "Default.yaml").read_text(encoding="utf-8"))
    variables = [v["nombre"] for v in contexto["variables"]]
    caso = yaml.safe_load((carpeta / "caso.yaml").read_text(encoding="utf-8"))
    entradas = [p.name for p in (carpeta / "entradas").glob("*.csv")]
    mapa = mapa_de_contexto(variables, entradas, caso.get("salidas", []))
    ruta_mapa = trabajo / "mapa.yaml"
    ruta_mapa.write_text(yaml.safe_dump(mapa), encoding="utf-8")
    resultado = _correr(
        ["tools/corpus_studio.py", "validar", nombre, "--jobs", str(paquete / "process"),
         "--padre", "job_programa", "--proyecto", os.environ.get("TALEND_PROJECT", str(_PROYECTO)),
         "--mapa", str(ruta_mapa), "--java-bin", os.environ.get("TALEND_JAVA_BIN", str(_JAVA)),
         "--m2", os.environ.get("TALEND_M2", str(_M2)), "--sufijo", sufijo]
    )
    print(f"--- {nombre} ---\n{resultado.stdout.strip()}\n{resultado.stderr.strip()}".rstrip())
    return resultado.returncode == 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    base = f"h{int(time.time()) % 100000}"
    fallos = 0
    for indice, nombre in enumerate(argv):
        if not validar(nombre, f"{base}{chr(97 + indice)}"):
            fallos += 1
    print(f"\n{len(argv)} casos, {len(argv) - fallos} coinciden")
    return 1 if fallos else 0


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
