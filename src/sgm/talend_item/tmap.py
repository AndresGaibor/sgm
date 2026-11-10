"""`tMap` de Talend: entradas, uniones, salidas y expresiones, como los guarda Studio 8.0.1.

Los parámetros salen de la plantilla `plantillas/tMap.json` (extraída de un Job real). Lo propio de
cada mapeo va en `<nodeData xsi:type="TalendMapper:MapperData">`, que Studio escribe después de los
`<metadata>`. La forma del bloque se comparó con `tests/fixtures/talend/tmap_nodedata.xml`.

Los nombres de atributo de uniones y rechazos salen del modelo EMF del mapper
(`org.talend.designer.mapper`: `InputTable.innerJoin`, `OutputTable.reject`,
`OutputTable.rejectInnerJoin`, `AbstractInOutTable.expressionFilter`) y de lo que lee el generador
(`components/tMap/tMap_main.inc.javajet`). Ningún Job real del proyecto tiene lookups ni rechazos,
así que el formato se valida ejecutando el Job en Studio.

La primera entrada es la principal; las demás son lookups. Cada columna de un lookup con expresión
en `expresiones_union` forma parte de la clave de unión, evaluada sobre la principal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.java_expressions import is_safe_java_expression
from sgm.java_identificadores import is_java_identifier
from sgm.talend_item.item import _atributo
from sgm.talend_item.modelo import Columna, Metadata, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla


@dataclass(frozen=True)
class EntradaMap:
    """Una entrada del tMap: la principal (`row1`) o un lookup (`row2`).

    En un lookup, `expresiones_union` asigna a cada columna de la unión su expresión de Java sobre
    la entrada principal (p. ej. `{"codigo": "row1.tipo"}`). `union_interna` activa el INNER JOIN:
    las filas principales sin pareja no salen por las salidas normales.
    """

    conexion: str
    columnas: list[Columna] = field(default_factory=list)
    # `matchingMode` de Studio: ALL_ROWS devuelve todas las parejas de la llave y UNIQUE_MATCH solo
    # la primera. Un `ON` de SQL es ALL_ROWS: la llave puede repetirse a la derecha y cada pareja es
    # una fila.
    union: str = "UNIQUE_MATCH"
    # `lookupMode` de Studio: LOAD_ONCE (el único visto en Jobs reales).
    lookup: str = "LOAD_ONCE"
    # Columna del lookup -> expresión de Java sobre la principal. Solo las columnas con
    # expresión forman la clave de unión.
    expresiones_union: dict[str, str] = field(default_factory=dict)
    # INNER JOIN (`innerJoin`): sin pareja, la fila principal se rechaza.
    union_interna: bool = False


@dataclass(frozen=True)
class SalidaMap:
    """Una salida del tMap: su nombre es el de la conexión que sale (`out1`).

    `rechazo_union` recoge las filas principales que no casan en el INNER JOIN ("catch inner join
    reject"). `rechazo` recoge las filas que descarta el filtro ("catch output reject"). `filtro` es
    una expresión booleana de Java que decide qué filas salen; vacío significa sin filtro.
    """

    nombre: str
    columnas: list[Columna] = field(default_factory=list)
    # Columna -> expresión de Java, p. ej. `row1.id * 2`. Toda columna necesita la suya.
    expresiones: dict[str, str] = field(default_factory=dict)
    rechazo_union: bool = False
    rechazo: bool = False
    filtro: str = ""


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


def _revisar_union(entradas: list[EntradaMap], salidas: list[SalidaMap]) -> None:
    """Comprueba que las uniones y los rechazos tengan lo que el generador de Studio necesita."""
    principal, *lookups = entradas
    if principal.union_interna or principal.expresiones_union:
        raise ValueError(f"La entrada principal '{principal.conexion}' no puede tener unión")
    for entrada in lookups:
        nombres = {c.nombre for c in entrada.columnas}
        sobran = sorted(set(entrada.expresiones_union) - nombres)
        if sobran:
            raise KeyError(f"El lookup '{entrada.conexion}' no tiene las columnas {sobran}")
        for columna, expresion in entrada.expresiones_union.items():
            if not expresion.strip():
                raise ValueError(
                    f"Falta la expresión de unión de la columna '{columna}' "
                    f"del lookup '{entrada.conexion}'"
                )
        if entrada.union_interna and not entrada.expresiones_union:
            raise ValueError(f"El INNER JOIN del lookup '{entrada.conexion}' no tiene unión")
    hay_inner_join = any(e.union_interna for e in lookups)
    for salida in salidas:
        if salida.rechazo_union and not hay_inner_join:
            raise ValueError(
                f"La salida '{salida.nombre}' recoge rechazos de unión, pero ningún lookup "
                "tiene INNER JOIN"
            )


def _nulable(columna: Columna) -> str:
    return ' nullable="true"' if columna.nulable else ""


def _revisar_seguridad(entradas: list[EntradaMap], salidas: list[SalidaMap]) -> None:
    """Valida nombres de esquema y expresiones en el límite público del tMap."""
    columnas = [c for entrada in entradas for c in entrada.columnas]
    columnas += [c for salida in salidas for c in salida.columnas]
    if any(not is_java_identifier(columna.nombre) for columna in columnas):
        raise ValueError("esquema tMap con identificadores Java no portables")
    expresiones = [
        *(
            expresion
            for entrada in entradas
            for expresion in entrada.expresiones_union.values()
        ),
        *(expresion for salida in salidas for expresion in salida.expresiones.values()),
        *(salida.filtro for salida in salidas if salida.filtro),
    ]
    if any(not is_safe_java_expression(expresion) for expresion in expresiones):
        raise ValueError("expresión Java de tMap con sintaxis no permitida")


def _conector(salida: SalidaMap) -> str:
    """Las salidas de rechazo van por una conexión REJECT; el resto, por FLOW."""
    return "REJECT" if salida.rechazo or salida.rechazo_union else "FLOW"


def _salida(salida: SalidaMap) -> list[str]:
    """`outputTables` de una salida, con sus marcas de rechazo y su filtro si los tiene."""
    marcas = ""
    if salida.rechazo:
        marcas += ' reject="true"'
    if salida.rechazo_union:
        marcas += ' rejectInnerJoin="true"'
    if salida.filtro.strip():
        marcas += f' expressionFilter="{_atributo(salida.filtro)}" activateExpressionFilter="true"'
    lineas = [
        f'      <outputTables sizeState="INTERMEDIATE" name="{_atributo(salida.nombre)}"{marcas}>'
    ]
    for c in salida.columnas:
        lineas.append(
            f'        <mapperTableEntries name="{_atributo(c.nombre)}" '
            f'expression="{_atributo(_expresion(salida, c))}" type="{c.tipo}"'
            f"{_nulable(c)}/>"
        )
    lineas.append("      </outputTables>")
    return lineas


def _entrada(entrada: EntradaMap) -> list[str]:
    """`inputTables` de una entrada; en un lookup, cada columna de unión lleva su expresión."""
    inner = ' innerJoin="true"' if entrada.union_interna else ""
    lineas = [
        f'      <inputTables sizeState="INTERMEDIATE" name="{_atributo(entrada.conexion)}" '
        f'matchingMode="{entrada.union}" lookupMode="{entrada.lookup}"{inner}>'
    ]
    for c in entrada.columnas:
        expresion = entrada.expresiones_union.get(c.nombre)
        extra = f' expression="{_atributo(expresion)}"' if expresion is not None else ""
        lineas.append(
            f'        <mapperTableEntries name="{_atributo(c.nombre)}"{extra} '
            f'type="{c.tipo}"{_nulable(c)}/>'
        )
    lineas.append("      </inputTables>")
    return lineas


def _datos(entradas: list[EntradaMap], salidas: list[SalidaMap]) -> str:
    """`<nodeData>` con la sangría de Studio: salidas primero, luego entradas."""
    lineas = [
        '    <nodeData xsi:type="TalendMapper:MapperData">',
        '      <uiProperties shellMaximized="true"/>',
        '      <varTables sizeState="INTERMEDIATE" name="Var" minimized="true"/>',
    ]
    for salida in salidas:
        _revisar_expresiones(salida)
        lineas += _salida(salida)
    for entrada in entradas:
        lineas += _entrada(entrada)
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
    """`tMap` con sus entradas y salidas. Cada salida da un bloque `<metadata>`, en orden.

    Que el nombre de cada conexión coincida con el de su entrada o salida es responsabilidad del
    llamador: el Job no se valida contra el grafo aquí.
    """
    if not entradas:
        raise ValueError("Un tMap necesita al menos una entrada")
    if not salidas:
        raise ValueError("Un tMap necesita al menos una salida")
    _revisar_seguridad(entradas, salidas)
    _revisar_union(entradas, salidas)
    nodo = nodo_desde_plantilla("tMap", unico, x, y, ruta_java=ruta_java)
    nodo.metadatas = [Metadata(_conector(s), s.nombre, tuple(s.columnas)) for s in salidas]
    nodo.datos = _datos(entradas, salidas)
    return nodo
