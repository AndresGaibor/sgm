"""Esquemas de las tablas que lee un programa, sin ningún YAML.

Por cada `PROC IMPORT`, el esquema de su tabla sale de la primera fuente que lo demuestre:

1. **Catálogo** (`env/schemas/`, origen `catalog`): los tipos son los del entorno.
2. **Cabecera del archivo de muestra** (origen `file_header`): da los nombres, no los tipos.
3. **Columnas que el programa usa aguas abajo** (origen `derived`): los nombres salen de las
   asignaciones, de las llaves de unión y de los filtros.

Una tabla que no llega al catálogo sale con `String`, el tipo por omisión documentado, y su
pendiente `P-TIPO-DESCONOCIDO` con la línea del `PROC IMPORT`: quien migre sabe que el tipo no está
demostrado. Un tipo numérico o una fecha nunca se suponen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sgm.ir.models import Column, Operator, Plan

# El tipo que se escribe cuando no hay ninguno demostrado; va siempre con su pendiente.
TIPO_POR_OMISION = "String"
_TIPO_DESCONOCIDO = "P-TIPO-DESCONOCIDO"
_REFERENCIA = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b")


@dataclass(frozen=True)
class PendienteMigracion:
    """Algo que el migrador no pudo resolver y que una persona tiene que completar o decidir."""

    codigo: str
    mensaje: str
    linea: int | None


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _nombre_base(tabla: str) -> str:
    """`work.clientes` -> `clientes`: como lo nombran las expresiones del SQL."""
    return tabla.split(".")[-1].lower()


def _textos(plan: Plan) -> list[str]:
    """Expresiones que pueden nombrar columnas: asignaciones, llaves, filtros y condiciones."""
    encontrados: list[str] = []
    for op in plan.graph.operators():
        params = op.params
        if op.kind == "filter":
            encontrados.append(str(params.get("expression") or ""))
        for asignacion in params.get("assignments") or []:
            encontrados.append(str(asignacion.get("expression") or ""))
        for llave in params.get("keys") or []:
            encontrados.extend(str(parte) for parte in llave)
        if params.get("condition"):
            encontrados.append(str(params["condition"]))
        for paso in params.get("steps") or []:
            propios = paso.get("params") or {}
            if paso.get("kind") == "filter":
                encontrados.append(str(propios.get("expression") or ""))
            for asignacion in propios.get("assignments") or []:
                encontrados.append(str(asignacion.get("expression") or ""))
            for llave in propios.get("keys") or []:
                encontrados.extend(str(parte) for parte in llave)
            if propios.get("condition"):
                encontrados.append(str(propios["condition"]))
    return [texto for texto in encontrados if texto]


def _columnas_usadas(plan: Plan, tabla: str) -> list[str]:
    """Columnas de `tabla` que el programa nombra en alguna expresión, en orden de aparición."""
    base = _nombre_base(tabla)
    vistas: dict[str, None] = {}
    for texto in _textos(plan):
        for prefijo, columna in _REFERENCIA.findall(texto):
            if prefijo.lower() == base:
                vistas.setdefault(columna.lower(), None)
    return list(vistas)


def _sin_comillas(texto: str) -> str:
    return texto.strip().strip("'\"")


def _ruta_de_muestra(muestra: Path | None, datafile: object) -> Path | None:
    """El archivo de muestra que corresponde al `DATAFILE` del paso, si se dio una carpeta."""
    if muestra is None or not datafile:
        return None
    nombre = Path(_sin_comillas(str(datafile)).replace("\\", "/")).name
    if muestra.is_file():
        return muestra if muestra.name == nombre else None
    candidata = muestra / nombre
    return candidata if candidata.is_file() else None


def _cabecera(ruta: Path, delimiter: str | None) -> list[str]:
    """Nombres de la primera línea del archivo, con el separador declarado o el que se vea."""
    try:
        primera = ruta.read_text(encoding="utf-8-sig", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return []
    separador = delimiter or (";" if ";" in primera else ",")
    return [_sin_comillas(campo) for campo in primera.split(separador) if campo.strip()]


def _de_catalogo(tabla: str, catalogo: dict[str, list[Column]]) -> list[Column] | None:
    columnas = catalogo.get(tabla)
    if columnas is None:
        return None
    return [Column(c.name, c.type, c.length, "catalog") for c in columnas]


def esquemas_de_entrada(
    plan: Plan, catalogo: dict[str, list[Column]], muestra: Path | None = None
) -> tuple[dict[str, list[Column]], list[PendienteMigracion]]:
    """Esquema de cada tabla que el plan lee y los pendientes de tipo que quedan."""
    esquemas: dict[str, list[Column]] = {}
    pendientes: list[PendienteMigracion] = []
    for op in plan.graph.operators():
        if op.kind != "read_file":
            continue
        salidas = [str(salida).lower() for salida in op.params.get("outputs") or []]
        if not salidas:
            continue
        tabla = salidas[0]
        demostrado = _de_catalogo(tabla, catalogo)
        if demostrado is not None:
            esquemas[tabla] = demostrado
            continue
        ruta = _ruta_de_muestra(muestra, op.params.get("datafile"))
        cabecera = _cabecera(ruta, op.params.get("delimiter")) if ruta else []
        if cabecera:
            origen = "file_header"
            nombres = cabecera
        else:
            origen = "derived"
            nombres = _columnas_usadas(plan, tabla)
        esquemas[tabla] = [Column(nombre, TIPO_POR_OMISION, None, origen) for nombre in nombres]
        pendientes.append(
            PendienteMigracion(
                _TIPO_DESCONOCIDO,
                f"{tabla}: {len(nombres)} columnas sin tipo demostrado; se escribe "
                f"{TIPO_POR_OMISION} hasta que haya catálogo o muestra",
                _linea(op),
            )
        )
    return esquemas, pendientes


__all__ = ["PendienteMigracion", "esquemas_de_entrada"]
