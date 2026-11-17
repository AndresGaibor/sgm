"""Lista las combinaciones de `OUTPUT` del espacio y cuántas migra `sgm migrar` (B-17).

Uso:
    uv run python tools/generar_combinaciones_output.py --listar

Por cada combinación escribe su programa en una carpeta temporal, la migra con `sgm migrar`
y cuenta:
las que salen sin pendiente de traducción, y las que quedan con pendiente (con su código). La
comparación con el oráculo la hacen las pruebas (`tests/unit/test_combinaciones_output.py`), no este
script.

`--escribir` escribe un caso por clase de equivalencia (108) en `tests/corpus/L6/`, con su
`esperado/` del oráculo independiente. Decisión 3 del dueño: una clase por caso, no las 386.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))
sys.path.insert(0, str(RAIZ / "src"))

from corpus_output.gramatica import DATASETS, combinaciones, representantes  # noqa: E402
from corpus_output.oraculo import esperado  # noqa: E402

# Mismas filas que usan las pruebas del espacio: incluyen un valor faltante.
ENTRADAS = [("a", "-1"), ("b", "0"), ("c", "3"), ("d", "5"), ("e", "")]
RAIZ_CORPUS = RAIZ / "tests" / "corpus" / "L6"


def _celda(valor) -> str:
    """Una celda del CSV: faltante vacío, entero sin decimales, o el número tal cual."""
    if valor is None or valor == "":
        return ""
    numero = float(valor)
    return str(int(numero)) if numero.is_integer() else repr(numero)


def _yaml_de(c, filas: dict[str, int]) -> str:
    tipos = ", ".join(
        "todos" if not d else ("uno" if len(d) == 1 else "par") for d in c.destinos
    )
    continuacion = "sí" if c.continuacion else "no"
    invariantes = "\n".join(f"- filas({d}) == {filas[d]}" for d in DATASETS)
    salidas = "\n".join(f"- {d}" for d in DATASETS)
    razon = (
        "Generado por tools/generar_combinaciones_output.py --escribir. Clase de rama "
        f"{c.rama}, destinos por bloque {tipos}, continuación {continuacion}. Esperado de un "
        "oráculo independiente que sigue lestmtsref, p. 273-274 (OUTPUT) y lrcon, p. 498 (la "
        "observación se escribe con el PDV)."
    )
    url = (
        "https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/docsets/"
        "lestmtsref/content/lestmtsref.pdf?locale=en"
    )
    return (
        "nivel: L6\nconstrucciones:\n- DATA STEP\n- OUTPUT\n"
        "capa: B\ntolerancia: 1.0e-06\norden_relevante: true\nestado: traducible\n"
        "origen: generado\n"
        f"salidas:\n{salidas}\n"
        f"razonamiento: '{razon}'\n"
        f"fuentes_url:\n- {url}\n"
        f"invariantes:\n{invariantes}\n"
    )


def escribir(raiz: Path = RAIZ_CORPUS) -> int:
    """Escribe un caso por clase de equivalencia y devuelve cuántos escribió."""
    casos = representantes()
    for indice, c in enumerate(casos, start=1):
        carpeta = raiz / f"l6_g{indice:03d}_{c.nombre.lower()}"
        (carpeta / "entradas").mkdir(parents=True, exist_ok=True)
        (carpeta / "esperado").mkdir(parents=True, exist_ok=True)
        (carpeta / "programa.sas").write_text(c.programa_sas(), encoding="utf-8")
        filas_entrada = "ID,VALOR\n" + "".join(f"{i},{v}\n" for i, v in ENTRADAS)
        (carpeta / "entradas" / "REGISTROS.csv").write_text(filas_entrada, encoding="utf-8")
        salida = esperado(c, [{"ID": i, "VALOR": v} for i, v in ENTRADAS])
        conteo: dict[str, int] = {}
        for d in DATASETS:
            filas = salida[d]
            conteo[d] = len(filas)
            lineas = "ID,VALOR\n" + "".join(
                f"{f['ID']},{_celda(f['VALOR'])}\n" for f in filas
            )
            (carpeta / "esperado" / f"{d}.csv").write_text(lineas, encoding="utf-8")
        (carpeta / "caso.yaml").write_text(_yaml_de(c, conteo), encoding="utf-8")
    return len(casos)

from sgm.cli_migrar import migrar  # noqa: E402


def listar() -> int:
    base = Path(tempfile.mkdtemp(prefix="combinaciones_output_"))
    muestra = base / "entradas"
    muestra.mkdir()
    (muestra / "REGISTROS.csv").write_text(
        "ID,VALOR\na,-1\nb,0\nc,3\nd,5\ne,\n", encoding="utf-8"
    )
    migran = 0
    codigos: Counter[str] = Counter()
    total = 0
    for c in combinaciones():
        total += 1
        programa = base / f"{c.nombre}.sas"
        programa.write_text(c.programa_sas(), encoding="utf-8")
        resultado = migrar(programa, base / c.nombre, muestra=muestra)
        reales = [
            p.codigo
            for p in resultado.pendientes
            if p.codigo not in {"P-TIPO-DESCONOCIDO", "P-CONFIGURACION-RESUELTA"}
        ]
        if reales:
            codigos.update(sorted(set(reales)))
        else:
            migran += 1
    print(f"combinaciones: {total}")
    print(f"se migran sin pendiente: {migran}")
    print(f"quedan con pendiente: {total - migran}")
    for codigo, n in codigos.most_common():
        print(f"  {codigo}: {n} combinaciones")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--listar", action="store_true", help="cuenta y clasifica las combinaciones",
    )
    parser.add_argument(
        "--escribir", action="store_true",
        help="escribe un caso por clase de equivalencia en tests/corpus/L6/",
    )
    args = parser.parse_args()
    if args.escribir:
        print(f"casos escritos: {escribir()}")
        return 0
    if not args.listar:
        parser.error("use --listar o --escribir")
    return listar()


if __name__ == "__main__":
    raise SystemExit(main())
