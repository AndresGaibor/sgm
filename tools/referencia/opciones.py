"""Extrae las opciones (propiedad y descripción) de las tablas de una página de Talend.

Las páginas traen una tabla por sección (`## Basic settings`, `## Advanced settings`...).
Cada fila es una propiedad con su descripción. El texto de las celdas se limpia del HTML que
el sitio mezcla en Markdown (`<br>`, `<span>`, `&gt;`...). El resultado es un YAML de consulta,
sin pasar por el esquema de reglas: no es una regla del compilador.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_ETIQUETA = re.compile(r"<[^>]+>")
_ESPACIOS = re.compile(r"\s+")
ENTIDADES = {"&gt;": ">", "&lt;": "<", "&amp;": "&", "&quot;": '"', "\\_": "_"}


def limpiar(celda: str) -> str:
    """Texto plano de una celda: sin etiquetas HTML, entidades ni espacios repetidos."""
    texto = celda.replace("<br>", " ").replace("<br/>", " ")
    texto = _ETIQUETA.sub(" ", texto)
    for entidad, reemplazo in ENTIDADES.items():
        texto = texto.replace(entidad, reemplazo)
    return _ESPACIOS.sub(" ", texto).strip()


def _filas(lineas: list[str]) -> list[tuple[str, str]]:
    """Filas de datos de una tabla Markdown (sin encabezado ni separador)."""
    filas: list[tuple[str, str]] = []
    for linea in lineas:
        if not linea.startswith("|"):
            break
        partes = [c.strip() for c in linea.strip().strip("|").split("|")]
        if (
            len(partes) < 2
            or set(partes[0]) <= {"-", " "}
            or partes[0] in ("Properties", "Variables")
        ):
            continue
        filas.append((limpiar(partes[0]), limpiar(partes[1])))
    return filas


def opciones_por_seccion(markdown: str) -> dict[str, list[dict[str, str]]]:
    """Secciones `## ...` de la página, con sus propiedades. Las secciones sin tabla se omiten."""
    resultado: dict[str, list[dict[str, str]]] = {}
    seccion: str | None = None
    lineas = markdown.splitlines()
    for i, linea in enumerate(lineas):
        if linea.startswith("## "):
            seccion = limpiar(linea[3:])
            continue
        if seccion and linea.startswith("| ") and (i == 0 or not lineas[i - 1].startswith("|")):
            filas = _filas(lineas[i:])
            if filas:
                resultado.setdefault(seccion, []).extend(
                    {"propiedad": p, "descripcion": d} for p, d in filas
                )
    return resultado


def escribir_yaml(origen: Path, destino: Path, titulo: str) -> int:
    """Escribe el YAML de consulta y devuelve el número de propiedades."""
    secciones = opciones_por_seccion(origen.read_text(encoding="utf-8"))
    datos = {
        "fuente": str(origen.name),
        "titulo": titulo,
        "nota": "Extracto de la documentación oficial. Consulta, no regla del compilador.",
        "secciones": [
            {"seccion": nombre, "propiedades": props} for nombre, props in secciones.items()
        ],
    }
    destino.write_text(
        yaml.safe_dump(datos, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )
    return sum(len(p) for p in secciones.values())
