"""Crea en Impala de pruebas las tablas que lee un programa SAS, o las de un CSV.

Uso (desde la raíz del repo):
  uv run python tools/contenedores/cargar_tablas.py --sas tests/fixtures/sas/client/client_large.sas
  uv run python tools/contenedores/cargar_tablas.py --csv RUTA.csv \
      --tabla biblioteca.tabla --ejecutar
Sin --ejecutar solo imprime el SQL (o lo guarda con --salida). Con --ejecutar lo corre en el
Impala del compose `tools/contenedores/impala` mediante el cliente de la imagen oficial.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fuentes_sas import tablas_base  # noqa: E402
from sql_carga import sentencias_desde_csv, sentencias_ficticias, sql_completo  # noqa: E402

RED = "sgmtest_impala_red"
CLIENTE = "apache/impala:4.5.3-impala_quickstart_client"
ANFITRION = "impalad:21050"


def ejecutar_sql(sql: str) -> subprocess.CompletedProcess[str]:
    """Ejecuta el script en Impala con impala-shell dentro de un contenedor efímero."""
    with tempfile.TemporaryDirectory(prefix="sgmtest_sql_") as carpeta:
        ruta = Path(carpeta) / "carga.sql"
        ruta.write_text(sql, encoding="utf-8")
        orden = [
            "docker", "run", "--rm", "--network", RED,
            "-v", f"{carpeta}:/sql:ro",
            "--entrypoint", "impala-shell", CLIENTE,
            "-i", ANFITRION, "-f", "/sql/carga.sql",
        ]  # fmt: skip
        return subprocess.run(orden, capture_output=True, text=True, check=False)


def construir_sql(args: argparse.Namespace) -> tuple[str, list[str]]:
    """SQL del programa o de los CSV, y los avisos de lo omitido."""
    bloques: list[list[str]] = []
    avisos: list[str] = []
    if args.sas:
        tablas, omitidas = tablas_base(Path(args.sas))
        bloques += [sentencias_ficticias(t, args.filas) for t in tablas]
        avisos += [f"OMITIDA {o.nombre}: {o.motivo}" for o in omitidas]
    if args.csv:
        if len(args.csv) != len(args.tabla or []):
            raise SystemExit("Cada --csv necesita su --tabla biblioteca.tabla")
        for ruta, destino in zip(args.csv, args.tabla, strict=True):
            biblioteca, tabla = destino.split(".")
            bloques.append(sentencias_desde_csv(biblioteca, tabla, Path(ruta)))
    if not bloques:
        raise SystemExit("Indica --sas o --csv con --tabla")
    return sql_completo(bloques), avisos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sas", help="Programa SAS del que sacar las tablas base")
    parser.add_argument("--csv", action="append", help="CSV con cabecera y filas reales")
    parser.add_argument("--tabla", action="append", help="biblioteca.tabla para cada --csv")
    parser.add_argument("--filas", type=int, default=3, help="Filas ficticias por tabla SAS")
    parser.add_argument("--salida", help="Guarda el SQL en esta ruta")
    parser.add_argument("--ejecutar", action="store_true", help="Ejecuta el SQL en Impala")
    args = parser.parse_args(argv)

    sql, avisos = construir_sql(args)
    for aviso in avisos:
        print(aviso)
    if args.salida:
        Path(args.salida).write_text(sql, encoding="utf-8")
        print(f"SQL guardado en {args.salida}")
    if not args.ejecutar:
        if not args.salida:
            print(sql)
        return 0
    resultado = ejecutar_sql(sql)
    print(resultado.stdout[-2000:])
    if resultado.returncode != 0 or "Could not execute" in resultado.stdout:
        print(resultado.stderr[-2000:], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
