"""Archivos externos en el flujo: PROC APPEND, IMPORT, EXPORT y DATA step con FILE/INFILE.

Un archivo es un dataset externo con clave estable `file:<ruta>`, con la ruta tal como aparece en
el programa. Un paso que escribe `file:<ruta>` y otro que lo lee quedan unidos como cualquier par
de datasets. Si nadie lo escribió antes, es una entrada externa del programa.

Las opciones de PROC se leen del texto del paso porque el parser general corta los valores entre
comillas con espacios (`datafile='C:\\mi carpeta\\x.csv'`).
"""

from __future__ import annotations

import re

from sgm.frontend.datastep import DataStep

PREFIJO_ARCHIVO = "file:"

# Valor entre comillas simples o dobles, o sin comillas (sin espacios ni paréntesis).
_OPCION = re.compile(r"""([A-Za-z_]\w*)\s*=\s*(?:'([^']*)'|"([^"]*)"|(\S+))""")
_NOMBRE_PROC = re.compile(r"(?is)^\s*proc\s+\S+")
# Solo rutas entre comillas: un `infile fileref;` o `file log;` no es una ruta.
_INFILE = re.compile(r"""(?i)^infile\s+(?:'([^']*)'|"([^"]*)")""")
_FILE = re.compile(r"""(?i)^file\s+(?:'([^']*)'|"([^"]*)")""")


def archivo(ruta: str) -> str:
    """Clave de dataset de un archivo externo, con la ruta como aparece en el programa."""
    return PREFIJO_ARCHIVO + ruta


def opciones_proc(texto: str) -> dict[str, str]:
    """Opciones de la sentencia PROC sin su nombre: clave en minúsculas y valor sin comillas."""
    resto = _NOMBRE_PROC.sub("", texto, count=1)
    opciones: dict[str, str] = {}
    for match in _OPCION.finditer(resto):
        valor = next(grupo for grupo in match.groups()[1:] if grupo is not None)
        opciones[match.group(1).lower()] = valor
    return opciones


def lecturas_escrituras_proc(nombre: str, texto: str) -> tuple[list[str], list[str]]:
    """Datasets y archivos que lee y escribe un PROC. APPEND lee DATA= y BASE=, y escribe BASE=."""
    opciones = opciones_proc(texto)
    if nombre == "append":
        reads = [opciones[k] for k in ("data", "base") if k in opciones]
        writes = [opciones["base"]] if "base" in opciones else []
    elif nombre == "import":
        reads = [archivo(opciones["datafile"])] if opciones.get("datafile") else []
        writes = [opciones["out"]] if "out" in opciones else []
    elif nombre == "export":
        reads = [opciones["data"]] if "data" in opciones else []
        writes = [archivo(opciones["outfile"])] if opciones.get("outfile") else []
    else:
        reads = [opciones["data"]] if "data" in opciones else []
        writes = [opciones["out"]] if "out" in opciones else []
    return reads, writes


def _agrega(destino: list[str], match: re.Match[str]) -> None:
    """Agrega la ruta del match (con comillas simples o dobles) si no está vacía."""
    ruta = next(grupo for grupo in match.groups() if grupo is not None)
    if ruta:
        destino.append(archivo(ruta))


def entradas_salidas_data_step(obj: DataStep) -> tuple[list[str], list[str]]:
    """Datasets que un DATA step lee (SET, MERGE, INFILE) y escribe (salidas, FILE).

    FILE LOG, FILE PRINT e INFILE DATALINES no son rutas y no cuentan.
    """
    reads = [
        ref["name"]
        for st in obj.statements
        if st.kind in ("set", "merge")
        for ref in st.fields.get("sources", [])
    ]
    writes = list(obj.outputs or [])
    for st in obj.statements:
        texto = st.text.strip()
        if m := _INFILE.match(texto):
            _agrega(reads, m)
        elif m := _FILE.match(texto):
            _agrega(writes, m)
    return reads, writes
