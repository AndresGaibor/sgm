"""Extracción de una plantilla de componente desde un nodo de un `.item` real.

Se conserva lo que Studio escribe por defecto y se neutraliza lo que es del Job de origen:
contraseñas, datos del entorno, código, consultas, el Job hijo, el mensaje y las columnas. Esas
columnas y las tablas por columna se regeneran al instanciar la plantilla con el esquema pedido.
"""

from __future__ import annotations

from xml.etree.ElementTree import Element

from sgm.talend_item.modelo import Columna

UNICO = "@@UNICO@@"  # marca del UNIQUE_NAME original dentro de los valores de la plantilla
IMPORT_POR_DEFECTO = "//import java.util.List;"
# Parámetros que son del Job de origen: nombre -> valor neutro. Se aplican a cualquier componente.
NEUTROS = {
    "LABEL": "__UNIQUE_NAME__",
    "MESSAGE": '""',
    "QUERY": '""',
    "TABLE": '""',
    "CODE": "",
    "IMPORT": IMPORT_POR_DEFECTO,
    "PROCESS": "",
    "PROCESS:PROCESS_TYPE_PROCESS": "",
    "PROCESS:PROCESS_TYPE_CONTEXT": "Default",
    "PREVIEW": "",  # imagen de vista previa del mapeo, un .bmp del Job de origen
}
# Datos del entorno de quien guardó el Job: se vacían.
SENSIBLES = frozenset({"USER", "HOST", "DBNAME", "PORT", "URL", "JDBC_URL", "FILENAME"})
TABLAS_VACIAS = frozenset({"CONTEXTPARAMS"})  # su contenido es del Job de origen
COLUMNA_REF = "SCHEMA_COLUMN"
# Tablas con una fila por columna del esquema y la forma que Studio les da (vistas en Jobs reales).
# Un Job guardado con el esquema vacío las deja sin filas; se recuperan de aquí.
POR_COLUMNA_CONOCIDAS = {
    "TRIMSELECT": [["TRIM", "false"]],
    "DECODE_COLS": [["DECODE", "false"]],
    "TRIM_COLUMN": [["TRIM", "false"]],
}


def columna_a_dict(c: Columna) -> dict[str, object]:
    return {
        "nombre": c.nombre,
        "tipo": c.tipo,
        "nulable": c.nulable,
        "clave": c.clave,
        "longitud": c.longitud,
        "precision": c.precision,
        "patron": c.patron,
    }


def _columna(e: Element) -> Columna:
    return Columna(
        e.get("name", ""),
        e.get("type", "id_String"),
        e.get("nullable", "true") == "true",
        e.get("key", "false") == "true",
        int(e.get("length", "-1")),
        int(e.get("precision", "-1")),
        e.get("pattern", ""),
    )


def _tabla(p: Element) -> dict[str, object]:
    celdas = [[v.get("elementRef", ""), v.get("value", "")] for v in p.findall("elementValue")]
    base: dict[str, object] = {"tabla": p.get("name", ""), "show": p.get("show")}
    if base["tabla"] in TABLAS_VACIAS:
        return base | {"celdas": []}
    if not celdas and base["tabla"] in POR_COLUMNA_CONOCIDAS:
        return base | {"por_columna": POR_COLUMNA_CONOCIDAS[str(base["tabla"])]}
    if celdas and celdas[0][0] == COLUMNA_REF:
        # Una fila por columna del esquema: la primera fila da la forma y los valores por defecto.
        ancho = next((i for i in range(1, len(celdas)) if celdas[i][0] == COLUMNA_REF), len(celdas))
        return base | {"por_columna": celdas[1:ancho]}
    return base | {"celdas": celdas}


def _valor(campo: str, nombre: str, valor: str, unico: str) -> str:
    if campo == "PASSWORD" or nombre in SENSIBLES:
        return ""
    if nombre in NEUTROS:
        return NEUTROS[nombre]
    return valor.replace(unico, UNICO)


def _metadatos(nodo: Element, unico: str) -> list[dict[str, object]]:
    """FLOW sin columnas (se piden al instanciar); los demás conectores reflejan al FLOW."""
    bloques = nodo.findall("metadata")
    flow = [_columna(c) for c in bloques[0].findall("column")] if bloques else []
    salida: list[dict[str, object]] = []
    for i, m in enumerate(bloques):
        columnas = [_columna(c) for c in m.findall("column")]
        base: dict[str, object] = {
            "conector": m.get("connector", "FLOW"),
            "nombre": (m.get("name") or "").replace(unico, UNICO),
        }
        if i == 0:
            salida.append(base | {"columnas": []})
        elif base["conector"] == "REJECT":
            # El rechazo repite las columnas del FLOW y añade las suyas (errorCode, errorMessage).
            propias = {c.nombre for c in flow}
            extra = [columna_a_dict(c) for c in columnas if c.nombre not in propias]
            salida.append(base | {"refleja_flow": True, "columnas": extra})
        else:
            salida.append(base | {"columnas": [columna_a_dict(c) for c in columnas]})
    return salida


def plantilla_desde_nodo(nodo: Element) -> dict[str, object]:
    """Plantilla de un `<node>` leído de un `.item` real: parámetros, tablas y metadatos."""
    parametros = nodo.findall("elementParameter")
    unico = next(p.get("value", "") for p in parametros if p.get("name") == "UNIQUE_NAME")
    filas: list[object] = []
    for p in parametros:
        nombre, campo = p.get("name", ""), p.get("field", "")
        if campo == "TABLE":
            filas.append(_tabla(p))
            continue
        valor = p.get("value")
        if valor is not None:
            valor = _valor(campo, nombre, valor, unico)
        filas.append([campo, nombre, valor, p.get("show")])
    return {
        "componente": nodo.get("componentName", ""),
        "version": nodo.get("componentVersion", ""),
        "parametros": filas,
        "metadatas": _metadatos(nodo, unico),
    }
