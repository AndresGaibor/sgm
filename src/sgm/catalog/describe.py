"""`sgm env import-describe` (F1.9): salida de `DESCRIBE <tabla>` de Impala a `env/schemas/`.

El archivo puede traer varias tablas. Cada tabla empieza con una línea que solo tiene su nombre
(`clientes` o `esquema.clientes`). Debajo va la salida de DESCRIBE, en tabla con barras
(`| name | type | comment |`) o separada por tabuladores (`nombre<TAB>tipo<TAB>comentario`).

El tipo se traduce a los de la IR (String, Integer, Long, Double, BigDecimal, Date, Boolean). Lo que
no tenga traducción queda con `type: null` y el tipo original en `impala`: nunca se inventa.
Si el esquema ya existe, sus tablas se actualizan y las demás se conservan.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ESQUEMAS = ROOT / "env" / "schemas"

TIPOS = {
    "string": "String",
    "varchar": "String",
    "char": "String",
    "int": "Integer",
    "integer": "Integer",
    "tinyint": "Integer",
    "smallint": "Integer",
    "bigint": "Long",
    "double": "Double",
    "float": "Double",
    "decimal": "BigDecimal",
    "timestamp": "Date",
    "date": "Date",
    "boolean": "Boolean",
}
_TIPO = re.compile(r"^\s*(\w+)\s*(?:\(\s*(\d+)(?:\s*,\s*(\d+))?\s*\))?\s*$")
_NOMBRE_DE_TABLA = re.compile(r"^[A-Za-z_][\w.]*$")
_ESQUEMA = re.compile(r"^[a-z0-9_]+$")
_BORDE = re.compile(r"^[\s+\-=|]*$")
_CABECERA = frozenset({"name", "col_name"})


@dataclass(frozen=True)
class Columna:
    name: str
    type: str | None
    length: int | None
    impala: str

    def como_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "length": self.length,
            "nullable": True,
            "impala": self.impala,
        }


def traducir(tipo_impala: str) -> tuple[str | None, int | None]:
    """Tipo de la IR y longitud (si la hay) para un tipo de Impala."""
    m = _TIPO.match(tipo_impala.lower())
    if not m:
        return None, None
    base, longitud = m.group(1), m.group(2)
    if base == "decimal":
        return "BigDecimal", None
    tipo = TIPOS.get(base)
    if tipo is None:
        return None, None
    if base in ("varchar", "char") and longitud:
        return tipo, int(longitud)
    return tipo, None


def _filas(texto: str) -> list[tuple[str, list[str]]]:
    """Líneas útiles: ('tabla', [nombre]) o ('columna', [nombre, tipo]).

    Los bordes y las cabeceras no entran.
    """
    filas: list[tuple[str, list[str]]] = []
    for linea in texto.splitlines():
        if not linea.strip() or _BORDE.match(linea):
            continue
        if "|" in linea:
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if len(celdas) >= 2 and celdas[0].lower() not in _CABECERA:
                filas.append(("columna", celdas[:2]))
        elif "\t" in linea:
            celdas = [c.strip() for c in linea.split("\t")]
            if len(celdas) >= 2 and celdas[0].lower() not in _CABECERA:
                filas.append(("columna", celdas[:2]))
        elif _NOMBRE_DE_TABLA.match(linea.strip()):
            filas.append(("tabla", [linea.strip()]))
    return filas


def parsear(texto: str, esquema: str) -> dict[str, list[Columna]]:
    """Tablas de la salida de DESCRIBE. Falla si una tabla no pertenece al esquema pedido."""
    tablas: dict[str, list[Columna]] = {}
    actual: str | None = None
    for clase, celdas in _filas(texto):
        if clase == "tabla":
            nombre = celdas[0].lower()
            if "." in nombre:
                prefijo, _, nombre = nombre.rpartition(".")
                if prefijo != esquema:
                    raise ValueError(f"la tabla {celdas[0]} no es del esquema {esquema}")
            actual = nombre
            tablas.setdefault(actual, [])
        else:
            if actual is None:
                raise ValueError(f"columna {celdas[0]} antes del nombre de su tabla")
            tipo, longitud = traducir(celdas[1])
            tablas[actual].append(Columna(celdas[0].lower(), tipo, longitud, celdas[1]))
    return {t: c for t, c in tablas.items() if c}


def importar(
    archivo: Path, esquema: str, destino: Path | None = None, hoy: dt.date | None = None
) -> tuple[Path, dict[str, list[Columna]]]:
    """Escribe `destino/<esquema>.json` con las tablas del archivo. Devuelve la ruta y las tablas.

    Sin `destino`, escribe en `env/schemas/` del proyecto.
    """
    if not _ESQUEMA.match(esquema):
        raise ValueError("el esquema debe ir en minúsculas, con letras, dígitos o _")
    tablas = parsear(archivo.read_text(encoding="utf-8", errors="replace"), esquema)
    if not tablas:
        raise ValueError(f"no encontré columnas en {archivo.name}")
    destino = ESQUEMAS if destino is None else destino
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / f"{esquema}.json"
    doc: dict = {"schema": esquema, "source": "DESCRIBE en Impala", "tables": {}}
    if ruta.exists():
        doc = json.loads(ruta.read_text(encoding="utf-8"))
    doc["captured"] = (hoy or dt.date.today()).isoformat()
    doc["tables"].update({t: [c.como_dict() for c in cols] for t, cols in tablas.items()})
    ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ruta, tablas
