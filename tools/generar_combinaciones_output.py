"""Lista las combinaciones de `OUTPUT` del espacio y cuántas migra `sgm migrar` (B-17).

Uso:
    uv run python tools/generar_combinaciones_output.py --listar

Por cada combinación escribe su programa en una carpeta temporal, la migra con `sgm migrar`
y cuenta:
las que salen sin pendiente de traducción, y las que quedan con pendiente (con su código). La
comparación con el oráculo la hacen las pruebas (`tests/unit/test_combinaciones_output.py`), no este
script. `--escribir N` (casos para `tests/corpus/L6/`) queda pendiente de B-17.
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

from corpus_output.gramatica import combinaciones  # noqa: E402

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
    args = parser.parse_args()
    if not args.listar:
        parser.error("use --listar (escribir casos aún no está en este hito)")
    return listar()


if __name__ == "__main__":
    raise SystemExit(main())
