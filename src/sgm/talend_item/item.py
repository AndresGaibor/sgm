"""Escritura del `.item` y el `.properties` de un Job de Talend Studio 8.0.

El `.item` sigue el formato que guarda Studio (XMI de `TalendFile.xsd`). No se ha abierto en Studio
desde este repositorio: la prueba compara contra un Job real guardado por Studio 8.0.1.
"""

from __future__ import annotations

import hashlib
from base64 import urlsafe_b64encode
from xml.sax.saxutils import escape

from sgm.talend_item.base import PARAMETROS_BASE
from sgm.talend_item.modelo import Columna, Conexion, Fila, Job, Metadata, Nodo, Tabla

PRODUCTO = "Talend Cloud Data Fabric"
VERSION_PRODUCTO = "8.0.1.20260925_1301-patch"
COLOR_SUBJOB = "0;93;185"
_ENCABEZADO = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<talendfile:ProcessType xmi:version="2.0" xmlns:xmi="http://www.omg.org/XMI" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xmlns:TalendMapper="http://www.talend.org/mapper" '
    'xmlns:talendfile="platform:/resource/org.talend.model/model/TalendFile.xsd" '
    'defaultContext="Default" jobType="Standard">\n'
)


def _atributo(valor: str) -> str:
    """Valor de atributo XML; los saltos y tabuladores se escriben como Studio, con referencias."""
    return escape(valor, {'"': "&quot;", "\n": "&#10;", "\t": "&#09;", "\r": "&#13;"})


def _fila(fila: Fila, sangria: str = "    ") -> str:
    campo, nombre, valor, show = fila
    partes = f'field="{campo}" name="{_atributo(nombre)}"'
    if valor is not None:
        partes += f' value="{_atributo(valor)}"'
    if show is not None:
        partes += f' show="{show}"'
    return f"{sangria}<elementParameter {partes}/>"


def _tabla(tabla: Tabla) -> list[str]:
    show = f' show="{tabla.show}"' if tabla.show is not None else ""
    lineas = [f'    <elementParameter field="TABLE" name="{tabla.nombre}"{show}>']
    for i, (ref, valor) in enumerate(tabla.celdas):
        lineas.append(
            f'      <elementValue elementRef="{_atributo(ref)}" '
            f'value="{_atributo(valor)}" id="{i}"/>'
        )
    lineas.append("    </elementParameter>")
    return lineas


def _columna(c: Columna) -> str:
    return (
        f'      <column comment="" defaultValue="" key="{str(c.clave).lower()}" '
        f'length="{c.longitud}" name="{_atributo(c.nombre)}" nullable="{str(c.nulable).lower()}" '
        f'pattern="{_atributo(c.patron)}" precision="{c.precision}" sourceType="" type="{c.tipo}" '
        f'originalLength="{c.longitud}" usefulColumn="true"/>'
    )


def _nodo(n: Nodo) -> list[str]:
    cabecera = (
        f'  <node componentName="{n.componente}" componentVersion="{n.version}" '
        f'offsetLabelX="0" offsetLabelY="0" posX="{n.x}" posY="{n.y}">'
    )
    lineas = [cabecera]
    for p in n.parametros:
        lineas += _tabla(p) if isinstance(p, Tabla) else [_fila(p)]
    if n.metadatas is None:
        bloques = [Metadata(n.conector, n.unico, tuple(n.columnas))]
    else:
        bloques = n.metadatas
    for bloque in bloques:
        nombre = _atributo(bloque.nombre)
        lineas.append(f'    <metadata connector="{bloque.conector}" name="{nombre}">')
        lineas += [_columna(c) for c in bloque.columnas]
        lineas.append("    </metadata>")
    if n.datos:
        lineas.append(n.datos)
    lineas.append("  </node>")
    return lineas


def _conexion(c: Conexion) -> list[str]:
    if c.parametros is None:
        filas = [
            ("CHECK", "MONITOR_CONNECTION", "false", None),
            ("TEXT", "UNIQUE_NAME", c.nombre, "false"),
        ]
    else:
        filas = list(c.parametros)
    return [
        f'  <connection connectorName="{c.conector}" label="{_atributo(c.etiqueta or c.nombre)}" '
        f'lineStyle="{c.estilo}" metaname="{c.origen}" offsetLabelX="0" offsetLabelY="0" '
        f'source="{c.origen}" target="{c.destino}">',
        *[_fila(f) for f in filas],
        "  </connection>",
    ]


def _subjobs(job: Job) -> list[str]:
    """Un subjob por nodo de inicio: los nodos que ninguna conexión de fila alimenta."""
    alimentados = {c.destino for c in job.conexiones if c.estilo in (0, 7)}
    lineas: list[str] = []
    for nodo in job.nodos:
        if nodo.unico in alimentados:
            continue
        lineas += [
            "  <subjob>",
            _fila(("TEXT", "UNIQUE_NAME", nodo.unico, "false")),
            _fila(("COLOR", "SUBJOB_TITLE_COLOR", COLOR_SUBJOB, "false")),
            _fila(("COLOR", "SUBJOB_COLOR", COLOR_SUBJOB, None)),
            "  </subjob>",
        ]
    return lineas


def render_item(job: Job) -> str:
    """Contenido del archivo `<job>_<versión>.item`."""
    lineas = [
        '  <context confirmationNeeded="false" hide="false" name="Default"/>',
        "  <parameters>",
    ]
    lineas += [_fila(f) for f in PARAMETROS_BASE]
    lineas.append("  </parameters>")
    for nodo in job.nodos:
        lineas += _nodo(nodo)
    for conexion in job.conexiones:
        lineas += _conexion(conexion)
    lineas += _subjobs(job)
    return _ENCABEZADO + "\n".join(lineas) + "\n</talendfile:ProcessType>\n"


def _id(semilla: str) -> str:
    """Identificador estable de 22 caracteres con la forma de los ids de Studio (`_` + base64)."""
    digest = hashlib.sha256(semilla.encode()).digest()[:16]
    return "_" + urlsafe_b64encode(digest).decode().rstrip("=")


def render_properties(job: Job, autor: str = "_0KqD4YE9EfGMqbenmdd8gw", fecha: str = "") -> str:
    """Contenido del archivo `<job>_<versión>.properties`. `fecha` es ISO 8601 con zona."""
    base = f"{job.nombre}_{job.version}"
    ids = {k: _id(f"{base}:{k}") for k in ("property", "item", "state")}
    extra = [
        ("created_product_fullname", PRODUCTO),
        ("created_product_version", VERSION_PRODUCTO),
        ("created_date", fecha),
        ("modified_product_fullname", PRODUCTO),
        ("modified_product_version", VERSION_PRODUCTO),
        ("modified_date", fecha),
    ]
    adicionales = "\n".join(
        f'    <additionalProperties xmi:id="{_id(f"{base}:a{i}")}" key="{k}" '
        f'value="{_atributo(v)}"/>'
        for i, (k, v) in enumerate(extra)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xmi:XMI xmi:version="2.0" xmlns:xmi="http://www.omg.org/XMI" '
        'xmlns:TalendProperties="http://www.talend.org/properties">\n'
        f'  <TalendProperties:Property xmi:id="{ids["property"]}" id="{_id(base + ":id")}" '
        f'label="{_atributo(job.nombre)}" version="{job.version}" statusCode="" '
        f'item="{ids["item"]}" displayName="{_atributo(job.nombre)}">\n'
        f'    <author href="../../talend.project#{autor}"/>\n'
        f"{adicionales}\n"
        "  </TalendProperties:Property>\n"
        f'  <TalendProperties:ItemState xmi:id="{ids["state"]}" path="{_atributo(job.nombre)}"/>\n'
        f'  <TalendProperties:ProcessItem xmi:id="{ids["item"]}" property="{ids["property"]}" '
        f'state="{ids["state"]}">\n'
        f'    <process href="{_atributo(base)}.item#/"/>\n'
        "  </TalendProperties:ProcessItem>\n"
        "</xmi:XMI>\n"
    )
