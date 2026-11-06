"""Esquemas de las tablas que lee un programa, sin ningún YAML.

Por cada `PROC IMPORT`, el esquema de su tabla sale de la primera fuente que lo demuestre:

1. **Catálogo** (`env/schemas/`, origen `catalog`): los tipos son los del entorno.
2. **Cabecera del archivo de muestra** (origen `file_header`): da los nombres, no los tipos.
3. **Columnas que el programa usa aguas abajo** (origen `derived`): los nombres salen de las
   asignaciones, de las llaves de unión y de los filtros.

Los nombres no son lo único que el programa demuestra: una columna que el SAS multiplica, divide,
suma o resta es numérica, porque en SAS solo los números se operan así, y una columna que se pasa a
`SUM`, `MEAN`, `ROUND` o a un `COALESCE` con un número también. Esas columnas salen `Double` —SAS
guarda todo número como doble— y no cuentan como tipo desconocido. Lo demás sale con `String`, el
tipo por omisión documentado, y su pendiente `P-TIPO-DESCONOCIDO` con la línea del `PROC IMPORT`:
quien migre sabe que el tipo no está demostrado. Un tipo numérico o una fecha nunca se suponen por
el nombre de la columna ni por el aspecto de sus datos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sgm.ir.models import Column, Operator, Plan
from sgm.migrar.esquemas_tipos import (
    TIPO_NUMERICO,
    TIPO_POR_OMISION,
    _columnas_numericas,
    _columnas_ordenadas,  # noqa: F401  (reexportación histórica)
    _textos,
    tipo_de_expresion,
)

_TIPO_DESCONOCIDO = "P-TIPO-DESCONOCIDO"
_REFERENCIA = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b")
# Identificador suelto que no es llamada a función: `select a, b from t` no califica las columnas.
_SUELTO = re.compile(r"\b([A-Za-z_]\w*)\b(?!\s*\()")
_CADENA = re.compile(r"'[^']*'|\"[^\"]*\"")
# Palabras del SQL que un identificador suelto puede ser sin ser una columna.
_PALABRAS = frozenset(
    {
        "and", "or", "not", "is", "null", "missing", "case", "when", "then", "else", "end",
        "true", "false", "between", "like", "in", "as", "distinct", "on", "select", "from",
        "where", "group", "order", "by", "having", "join", "left", "right", "inner", "outer",
        "desc", "asc", "work",
    }
)


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


def _columnas_usadas(plan: Plan, tabla: str) -> list[str]:
    """Columnas de `tabla` que el programa nombra en alguna expresión, en orden de aparición."""
    base = _nombre_base(tabla)
    vistas: dict[str, None] = {}
    for texto in _textos(plan):
        for prefijo, columna in _REFERENCIA.findall(texto):
            if prefijo.lower() == base:
                vistas.setdefault(columna.lower(), None)
    for columna in _columnas_sueltas(plan, base):
        vistas.setdefault(columna.lower(), None)
    return list(vistas)


def _entradas(plan: Plan, op: Operator) -> set[str]:
    """Conjuntos que lee el operador, sin librería: sus `read` o los productores de sus entradas."""
    nombres: set[str] = set()
    for previo in plan.graph.predecessors(op.id):
        anterior = plan.graph.operator(previo)
        if anterior.kind == "read":
            nombres.add(_nombre_base(str(anterior.params.get("dataset") or "")))
            continue
        for salida in anterior.params.get("outputs") or []:
            nombres.add(_nombre_base(str(salida)))
    return {nombre for nombre in nombres if nombre}


def _identificadores(texto: str) -> list[str]:
    """Identificadores sueltos de una expresión: sin cadenas, sin referencias calificadas, sin
    palabras del SQL y sin llamadas a función."""
    limpio = _REFERENCIA.sub(" ", _CADENA.sub(" ", texto))
    return [nombre for nombre in _SUELTO.findall(limpio) if nombre.lower() not in _PALABRAS]


def _sueltos(op: Operator) -> list[str]:
    """Identificadores que son una columna entera: asignación, llave, `KEEP` o filtro."""
    nombres: list[str] = []
    grupos = [op.params, *(paso.get("params") or {} for paso in op.params.get("steps") or [])]
    for grupo in grupos:
        nombres.extend(str(nombre) for nombre in grupo.get("names") or [])
        # Las llaves de un ORDER BY o de un DISTINCT son columnas de la entrada; una posición
        # (`ORDER BY 2`) no nombra ninguna.
        nombres.extend(str(n) for n in grupo.get("by") or [] if not str(n).strip().isdigit())
        for asignacion in grupo.get("assignments") or []:
            expresion = str(asignacion.get("expression") or "")
            if asignacion.get("origin") == "columna":
                nombres.append(expresion.split(".")[-1])
            else:
                nombres.extend(_identificadores(expresion))
        for llave in grupo.get("keys") or []:
            nombres.extend(str(parte).split(".")[-1] for parte in llave)
        textos = [str(grupo.get("condition") or ""), str(grupo.get("expression") or "")]
        for texto in textos:
            nombres.extend(_identificadores(texto))
    return [nombre for nombre in nombres if nombre]


def _columnas_sueltas(plan: Plan, base: str) -> list[str]:
    """Columnas sin calificar, solo cuando el operador lee una única tabla.

    `select a, b from work.clientes` no dice `clientes.a`, pero tampoco deja dudas: hay una sola
    tabla. Con dos tablas el nombre suelto puede ser de cualquiera, y entonces no se atribuye.
    """
    vistas: dict[str, None] = {}
    for op in plan.graph.operators():
        if _entradas(plan, op) != {base}:
            continue
        for nombre in _sueltos(op):
            vistas.setdefault(nombre.lower(), None)
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
    numericas = _columnas_numericas(plan)
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
        if op.params.get("input_names"):
            origen = "sas_input"
            nombres = [str(nombre) for nombre in op.params["input_names"]]
        elif cabecera:
            origen = "file_header"
            nombres = cabecera
        else:
            origen = "derived"
            nombres = _columnas_usadas(plan, tabla)
        esquemas[tabla] = [
            Column(
                nombre,
                TIPO_NUMERICO if nombre.lower() in numericas else TIPO_POR_OMISION,
                None,
                origen,
            )
            for nombre in nombres
        ]
        sin_tipo = [nombre for nombre in nombres if nombre.lower() not in numericas]
        if not sin_tipo:
            continue
        pendientes.append(
            PendienteMigracion(
                _TIPO_DESCONOCIDO,
                f"{tabla}: {len(sin_tipo)} de {len(nombres)} columnas sin tipo demostrado; se "
                f"escriben {TIPO_POR_OMISION} hasta que haya catálogo o muestra",
                _linea(op),
            )
        )
    return esquemas, pendientes


__all__ = ["PendienteMigracion", "esquemas_de_entrada", "tipo_de_expresion"]
