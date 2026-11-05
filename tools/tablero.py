"""Tablero del proyecto: la fotografía de la sección 2 de `ruta-a-produccion.md` en un comando.

Uso:
    uv run python tools/tablero.py               medidas sin Studio ni MCP
    uv run python tools/tablero.py --suite       añade el resultado de `pytest -q`
    uv run python tools/tablero.py --markdown    solo la tabla, para pegarla en un hito

Mide lo que se puede medir sin Studio: componentes por Job emitido, conformidad de la referencia
manual contra el diseño que sale del SAS, casos del corpus por nivel y estado, pendientes del modelo
agrupados por motivo y construcciones del SAS cubiertas por el corpus. Lo que necesita Studio
(Jobs ejecutados en el editor) no lo mide este comando y queda escrito como no medido.

Código de salida: 0 siempre, salvo un error de lectura o de sgm (2). El que falla por umbrales es
`tools/ci.py`.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections import Counter
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROGRAMA_DEFECTO = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
CORPUS_DEFECTO = REPO / "tests" / "corpus"
for ruta in (REPO, REPO / "tools"):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

_NODO = re.compile(r"<node\b")
_RESUMEN_PYTEST = re.compile(r"^(?P<resultado>.*?)\s+in\s+[\d.]+s")


@lru_cache(maxsize=4)
def componentes(programa: Path) -> dict[str, int]:
    """Emite los Jobs del programa con `sgm talend` y cuenta los `<node>` de cada `.item`.

    El resultado se memoriza: emitir el programa grande tarda segundos y el tablero lo pide varias
    veces. No se modifica el diccionario devuelto (lo comparten las llamadas).
    """
    with tempfile.TemporaryDirectory(prefix="tablero-") as temporal:
        salida = subprocess.run(
            [sys.executable, "-m", "sgm.cli", "talend", str(programa), "--out", temporal],
            cwd=REPO,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if salida.returncode != 0:
            raise RuntimeError(f"sgm talend falló: {salida.stderr[-800:]}")
        proceso = Path(temporal) / programa.stem / "talend" / "process"
        conteo = {}
        for item in sorted(proceso.glob("*.item")):
            nombre = re.sub(r"_\d+(?:\.\d+)*\.item$", "", item.name)
            conteo[nombre] = len(_NODO.findall(item.read_text(encoding="utf-8", errors="replace")))
        return conteo


def conformidad() -> dict[str, int]:
    """Filas y secciones de la referencia manual que el diseño emitido ya cumple.

    Son las mismas cuentas que hacen las pruebas de `tests/conformidad`: una fila se cumple si su
    sección ya se emite y no está en `DIFERENCIAS_CONOCIDAS` ni en `FILAS_PENDIENTES`; una sección,
    si está en `SECCIONES_EMITIDAS`.
    """
    from sgm.proceso.diseno_doc import SECCIONES_EMITIDAS
    from tests.conformidad.cargador import todas_las_filas
    from tests.conformidad.test_conformidad import (
        DIFERENCIAS_CONOCIDAS,
        FILAS_PENDIENTES,
        SECCIONES,
    )

    filas = todas_las_filas(SECCIONES)
    cumplidas = [
        fila
        for fila in filas
        if fila.seccion in SECCIONES_EMITIDAS
        and fila.id not in DIFERENCIAS_CONOCIDAS
        and fila.id not in FILAS_PENDIENTES
    ]
    return {
        "filas": len(filas),
        "filas_cumplidas": len(cumplidas),
        "secciones": len(SECCIONES),
        "secciones_emitidas": len(set(SECCIONES) & set(SECCIONES_EMITIDAS)),
    }


@lru_cache(maxsize=4)
def pendientes(programa: Path) -> list[tuple[str, str]]:
    """Pendientes del modelo del programa grande, cada uno con su motivo (los del diseño)."""
    from sgm.proceso.diseno_doc import construir_documento

    decisiones = REPO / "decisiones"
    documento = construir_documento(
        programa,
        decisiones / f"{programa.stem}.agrupacion.yaml",
        decisiones / f"{programa.stem}.diseno.yaml",
    )
    return documento.pendientes


def corpus(carpeta: Path) -> dict[str, object]:
    """Casos del corpus por nivel, por estado y construcciones del SAS que cubren."""
    from corpus_lib.caso import todos_los_casos

    casos = todos_los_casos(carpeta)
    por_nivel = Counter(caso.nivel for caso in casos)
    por_estado = Counter(caso.estado for caso in casos)
    con_esperado = sum(
        1 for caso in casos if caso.esperado.is_dir() and any(caso.esperado.iterdir())
    )
    todas = {construccion for caso in casos for construccion in caso.construcciones}
    traducibles = {
        construccion
        for caso in casos
        if caso.estado == "traducible"
        for construccion in caso.construcciones
    }
    return {
        "casos": len(casos),
        "por_nivel": dict(sorted(por_nivel.items(), key=lambda par: int(par[0][1:]))),
        "por_estado": dict(sorted(por_estado.items())),
        "con_esperado": con_esperado,
        "construcciones": len(todas),
        "construcciones_traducibles": len(traducibles),
    }


def suite(ruta: Path = REPO) -> str:
    """Corre `pytest -q` y devuelve la línea de resumen (`N passed, M skipped ... in Xs`)."""
    salida = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(ruta)],
        cwd=REPO,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    lineas = [linea.strip() for linea in salida.stdout.splitlines() if linea.strip()]
    if not lineas:
        return "sin resumen"
    ultima = lineas[-1]
    coincide = _RESUMEN_PYTEST.match(ultima)
    return coincide.group("resultado") if coincide else ultima


def filas_tablero(programa: Path, carpeta_corpus: Path, con_suite: bool) -> list[tuple[str, str]]:
    """Las filas de la tabla, en el orden de la sección 2 del plan."""
    jobs = componentes(programa)
    conf = conformidad()
    pen = pendientes(programa)
    motivos = Counter(motivo for _, motivo in pen)
    datos = corpus(carpeta_corpus)
    filas = [
        (
            "Componentes emitidos por `sgm talend client_large.sas`",
            f"{sum(jobs.values())} ({', '.join(f'{j} {n}' for j, n in jobs.items())}); "
            "meta N1 unos 80",
        ),
        (
            "Conformidad contra el diseño manual",
            f"{conf['filas_cumplidas']} de {conf['filas']} filas y {conf['secciones_emitidas']} "
            f"de {conf['secciones']} secciones",
        ),
        (
            "Pendientes del modelo para el programa grande",
            f"{len(pen)}, en {len(motivos)} motivos",
        ),
        (
            "Casos del corpus",
            f"{datos['casos']} ({', '.join(f'{n} {c}' for n, c in datos['por_nivel'].items())}); "
            f"{datos['con_esperado']} con archivos en `esperado/`",
        ),
        (
            "Casos del corpus por estado",
            ", ".join(f"{estado} {n}" for estado, n in datos["por_estado"].items()),
        ),
        (
            "Cobertura de construcciones del SAS",
            f"{datos['construcciones']} construcciones distintas en el corpus; "
            f"{datos['construcciones_traducibles']} aparecen en casos `traducible`",
        ),
        (
            "Casos traducidos por un traductor automático y pasados en Studio",
            "no hay traductor general: R7-01 a R7-18 del plan",
        ),
    ]
    if con_suite:
        filas.append(("Suite", suite()))
    return filas


def tabla(filas: list[tuple[str, str]]) -> str:
    """Tabla Markdown de dos columnas, como la de la sección 2 del plan."""
    lineas = ["| Medida | Valor |", "|---|---|"]
    lineas += [f"| {medida} | {valor} |" for medida, valor in filas]
    return "\n".join(lineas) + "\n"


def detalle_motivos(programa: Path) -> list[tuple[str, int]]:
    """Pendientes contados por motivo, de mayor a menor."""
    return Counter(motivo for _, motivo in pendientes(programa)).most_common()


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--programa", type=Path, default=PROGRAMA_DEFECTO)
    parser.add_argument("--corpus", type=Path, default=CORPUS_DEFECTO)
    parser.add_argument("--suite", action="store_true", help="añade el resultado de `pytest -q`")
    parser.add_argument(
        "--markdown", action="store_true", help="no escribe los pendientes por motivo"
    )
    args = parser.parse_args(argv)
    try:
        sistema = tabla(filas_tablero(args.programa, args.corpus, args.suite))
        motivos = detalle_motivos(args.programa)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    sys.stdout.write(sistema)
    if not args.markdown:
        print("\n## Pendientes por motivo\n")
        for motivo, cantidad in motivos:
            print(f"- {cantidad}: {motivo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
