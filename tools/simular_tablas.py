"""Emulador de las tablas Impala: un CSV por tabla, con las columnas que el SAS usa de ella.

Uso: uv run python tools/simular_tablas.py <programa.sas> <carpeta_salida> [--filas N]

Lee las consultas `connect to IMPALA ... select * from connection to IMPALA (...)` del programa,
saca la tabla de cada `FROM` y las columnas que la consulta referencia (calificadas con su alias y,
si van en la lista del `SELECT`, sin calificar) y escribe `<carpeta>/<biblioteca>.<tabla>.csv` con
cabecera y N filas de datos evidentemente falsos (`SIM_<columna>_<n>`). Nunca se copian datos
reales.

Tambien deja `<carpeta>/CONVENCION.md` con la regla que deben seguir los Jobs: leer la tabla con
`tImpalaInput` en produccion y, cuando el contexto `modo_simulacion` no este vacio, leer el CSV.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable
from pathlib import Path

_CONSULTA = re.compile(r"(?is)\bconnection\s+to\s+IMPALA\s*\(")
_FROM = re.compile(r"(?is)\bFROM\s+(?P<tabla>[\w.]+)(?:\s+(?:AS\s+)?(?P<alias>\w+))?")
_SELECT = re.compile(r"(?is)\bSELECT\b(?P<lista>.*?)(?=\bFROM\b|$)")
_AS = re.compile(r"(?is)\s*as\s+\w+$")
_FUNCION = re.compile(r"\w+\s*\(")
_RESERVADAS = frozenset(
    {
        "ALL",
        "AS",
        "CASE",
        "DISTINCT",
        "END",
        "FROM",
        "GROUP",
        "HAVING",
        "LIMIT",
        "NOW",
        "ORDER",
        "SELECT",
        "THEN",
        "WHEN",
        "WHERE",
    }
)
CONVENCION = """# Simulacion de tablas Impala

Los Jobs que leen Impala eligen el origen con el contexto `modo_simulacion`:

- vacio (produccion): `tImpalaInput` contra `<biblioteca>.<tabla>`.
- `1` (simulacion): `tFileInputDelimited` contra `<ruta_simulacion>/<biblioteca>.<tabla>.csv`,
  con `FIELDSEPARATOR=";"` e `INCLUDEHEADER=true`.

Los CSV de esta carpeta los genera `tools/simular_tablas.py` con las columnas que el SAS usa de
cada tabla. No son datos reales: son valores `SIM_<columna>_<n>`.
"""


def consultas_impala(texto: str) -> list[str]:
    """SQL interno de cada bloque `select * from connection to IMPALA (...)`."""
    consultas: list[str] = []
    for m in _CONSULTA.finditer(texto):
        cierre = _cierre(texto, m.end() - 1)
        if cierre is not None:
            consultas.append(texto[m.end() : cierre])
    return consultas


def tablas_impala(texto: str) -> dict[str, list[str]]:
    """Columnas que el programa usa de cada tabla Impala, sin repetir y en orden de aparicion."""
    resultado: dict[str, list[str]] = {}
    for sql in consultas_impala(texto):
        for tabla, columnas in _columnas_por_tabla(sql):
            resultado[tabla] = _unicas([*resultado.get(tabla, []), *columnas])
    return resultado


def simular(texto: str, carpeta: Path, filas: int) -> list[str]:
    """Escribe un CSV por tabla Impala y la convencion; una linea de reporte por archivo."""
    carpeta.mkdir(parents=True, exist_ok=True)
    lineas: list[str] = []
    for tabla, columnas in tablas_impala(texto).items():
        destino = carpeta / f"{tabla}.csv"
        cabecera = columnas or ["PENDIENTE"]
        cuerpo = [
            ";".join(f"SIM_{columna}_{n}" for columna in cabecera)
            for n in range(1, filas + 1)
        ]
        destino.write_text(
            "\n".join([";".join(cabecera), *cuerpo]) + "\n", encoding="utf-8", newline="\n"
        )
        resumen = f"{len(columnas)} columnas" if columnas else "PENDIENTE: el SAS no usa columnas"
        lineas.append(f"{destino.name}: {resumen}, {filas} filas simuladas")
    (carpeta / "CONVENCION.md").write_text(CONVENCION, encoding="utf-8", newline="\n")
    return lineas


def _cierre(texto: str, abre: int) -> int | None:
    """Posicion del parentesis que cierra el de `abre`, contando anidados."""
    profundidad = 0
    for i in range(abre, len(texto)):
        if texto[i] == "(":
            profundidad += 1
        elif texto[i] == ")":
            profundidad -= 1
            if profundidad == 0:
                return i
    return None


def _columnas_por_tabla(sql: str) -> list[tuple[str, list[str]]]:
    """Una pareja `(tabla, columnas)` por cada `FROM`, si la tabla es de Impala."""
    resultado: list[tuple[str, list[str]]] = []
    for indice, m in enumerate(_FROM.finditer(sql)):
        tabla = m.group("tabla")
        if "." not in tabla:
            continue  # dataset de SAS o marcador de macro: no es tabla Impala
        alias = m.group("alias")
        if alias is not None and alias.upper() in _RESERVADAS:
            alias = None
        calificadores = {tabla.rsplit(".", 1)[-1].casefold()}
        if alias:
            calificadores.add(alias.casefold())
        columnas = _calificadas(sql, calificadores)
        if indice == 0:
            columnas = _unicas([*_desnudas(sql), *columnas])
        resultado.append((tabla, columnas))
    return resultado


def _calificadas(sql: str, calificadores: set[str]) -> list[str]:
    """Columnas referenciadas como `alias.columna` o `tabla.columna`."""
    halladas: list[str] = []
    for calificador in calificadores:
        patron = re.compile(r"(?i)(?<![\w.])" + re.escape(calificador) + r"\.(\w+)")
        halladas.extend(m.group(1) for m in patron.finditer(sql))
    return halladas


def _desnudas(sql: str) -> list[str]:
    """Columnas de la lista del `SELECT` que van sin calificar, dentro de una funcion o no."""
    lista = _SELECT.search(sql)
    if lista is None:
        return []
    halladas: list[str] = []
    for trozo in lista.group("lista").split(","):
        expresion = _AS.sub("", trozo.strip())
        for nombre in re.findall(r"\w+", _FUNCION.sub("", expresion)):
            if nombre.upper() in _RESERVADAS or nombre.isdigit():
                continue
            halladas.append(nombre)
    return halladas


def _unicas(nombres: Iterable[str]) -> list[str]:
    """Quita repetidos sin distinguir mayusculas y conserva la primera aparicion."""
    vistos: set[str] = set()
    salida: list[str] = []
    for nombre in nombres:
        clave = nombre.casefold()
        if clave not in vistos:
            vistos.add(clave)
            salida.append(nombre)
    return salida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera CSV simulados de las tablas Impala.")
    parser.add_argument("programa", type=Path, help="Programa SAS a analizar")
    parser.add_argument("carpeta", type=Path, help="Carpeta donde escribir los CSV")
    parser.add_argument("--filas", type=int, default=5, help="Filas simuladas por tabla")
    args = parser.parse_args(argv)
    if args.filas < 0:
        parser.error("--filas no puede ser negativo")
    texto = args.programa.read_text(encoding="utf-8", errors="replace")
    for linea in simular(texto, args.carpeta, args.filas):
        print(linea)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
