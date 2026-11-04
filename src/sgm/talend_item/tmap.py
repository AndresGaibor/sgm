"""`tMap` de Talend: entradas, salidas y expresiones de mapeo, tal como las guarda Studio 8.0.1.

Los parámetros salen de la plantilla `plantillas/tMap.json` (extraída de un Job real). Lo propio de
cada mapeo va en `<nodeData xsi:type="TalendMapper:MapperData">`, que Studio escribe después de los
`<metadata>`. La forma del bloque se comparó con `tests/fixtures/talend/tmap_nodedata.xml`.

Solo se soporta lo que aparece en Jobs reales: entradas principales con `matchingMode` y
`lookupMode`, salidas con expresión por columna. No hay filtros, variables ni joins de búsqueda
(lookup) con varias entradas en los ejemplos; si se piden, se añaden cuando exista un ejemplo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.talend_item.item import _atributo
from sgm.talend_item.modelo import Columna, Metadata, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla


@dataclass(frozen=True)
class EntradaMap:
    """Una entrada del tMap; `conexion` es el nombre de la conexión que llega (`row1`)."""

    conexion: str
    columnas: list[Columna] = field(default_factory=list)
    # `matchingMode` de Studio: UNIQUE_MATCH o ALL_ROWS (vistos en Jobs reales).
    union: str = "UNIQUE_MATCH"
    # `lookupMode` de Studio: LOAD_ONCE (el único visto en Jobs reales).
    lookup: str = "LOAD_ONCE"


@dataclass(frozen=True)
class SalidaMap:
    """Una salida del tMap: su nombre es el de la conexión que sale (`out1`)."""

    nombre: str
    columnas: list[Columna] = field(default_factory=list)
    # Columna -> expresión de Java, p. ej. `row1.id * 2`. Toda columna necesita la suya.
    expresiones: dict[str, str] = field(default_factory=dict)


def _expresion(salida: SalidaMap, columna: Columna) -> str:
    if columna.nombre not in salida.expresiones:
        raise KeyError(
            f"La columna '{columna.nombre}' de la salida '{salida.nombre}' no tiene expresión"
        )
    return salida.expresiones[columna.nombre]


def _revisar_expresiones(salida: SalidaMap) -> None:
    """Rechaza expresiones de columnas que la salida no tiene: un nombre mal escrito no se calla."""
    nombres = {c.nombre for c in salida.columnas}
    sobran = sorted(set(salida.expresiones) - nombres)
    if sobran:
        raise KeyError(f"La salida '{salida.nombre}' no tiene las columnas {sobran}")


def _nulable(columna: Columna) -> str:
    return ' nullable="true"' if columna.nulable else ""


def _datos(entradas: list[EntradaMap], salidas: list[SalidaMap]) -> str:
    """`<nodeData>` con la sangría de Studio: salidas primero, luego entradas."""
    lineas = [
        '    <nodeData xsi:type="TalendMapper:MapperData">',
        '      <uiProperties shellMaximized="true"/>',
        '      <varTables sizeState="INTERMEDIATE" name="Var" minimized="true"/>',
    ]
    for salida in salidas:
        _revisar_expresiones(salida)
        lineas.append(
            f'      <outputTables sizeState="INTERMEDIATE" name="{_atributo(salida.nombre)}">'
        )
        for c in salida.columnas:
            lineas.append(
                f'        <mapperTableEntries name="{_atributo(c.nombre)}" '
                f'expression="{_atributo(_expresion(salida, c))}" type="{c.tipo}"'
                f"{_nulable(c)}/>"
            )
        lineas.append("      </outputTables>")
    for entrada in entradas:
        lineas.append(
            f'      <inputTables sizeState="INTERMEDIATE" name="{_atributo(entrada.conexion)}" '
            f'matchingMode="{entrada.union}" lookupMode="{entrada.lookup}">'
        )
        for c in entrada.columnas:
            lineas.append(
                f'        <mapperTableEntries name="{_atributo(c.nombre)}" type="{c.tipo}"'
                f"{_nulable(c)}/>"
            )
        lineas.append("      </inputTables>")
    lineas.append("    </nodeData>")
    return "\n".join(lineas)


def tmap(
    unico: str,
    entradas: list[EntradaMap],
    salidas: list[SalidaMap],
    x: int = 0,
    y: int = 0,
    ruta_java: str | None = None,
) -> Nodo:
    """`tMap` con sus entradas y salidas. Cada salida da un bloque `<metadata>` FLOW, en orden.

    Que el nombre de cada conexión de salida coincida con el de su salida es responsabilidad del
    llamador: el Job no se valida contra el grafo aquí.
    """
    if not salidas:
        raise ValueError("Un tMap necesita al menos una salida")
    nodo = nodo_desde_plantilla("tMap", unico, x, y, ruta_java=ruta_java)
    nodo.metadatas = [Metadata("FLOW", s.nombre, tuple(s.columnas)) for s in salidas]
    nodo.datos = _datos(entradas, salidas)
    return nodo
