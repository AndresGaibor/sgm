"""Reglas de secretos sobre atributos XML de `.item` y `.properties` de Talend.

Un parámetro es sensible si su `field` es `PASSWORD` o `ENCRYPTED`, o si el parámetro de contexto
es de tipo `id_Password`. Su `value` debe estar vacío, ser `***` o referenciar un contexto.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterator
from dataclasses import dataclass

from sgm.seguridad.enmascarado import es_marcador
from sgm.seguridad.lista_blanca import permitido

_ETIQUETA = re.compile(r"<(\w+)((?:\s+[\w:.-]+=\"[^\"]*\")*)\s*/?>")
_ATRIBUTO = re.compile(r'([\w:.-]+)="([^"]*)"')
CAMPOS_SENSIBLES = frozenset({"PASSWORD", "ENCRYPTED"})


@dataclass(frozen=True)
class HallazgoXml:
    linea: int
    tipo: str
    valor: str  # valor completo: quien lo consume debe enmascararlo antes de mostrarlo


def _atributos(cadena: str) -> dict[str, str]:
    return {k: html.unescape(v) for k, v in _ATRIBUTO.findall(cadena)}


def hallazgos_xml(texto: str) -> Iterator[HallazgoXml]:
    """Recorre las etiquetas en orden y reporta los PASSWORD y contextos `id_Password` con valor."""
    componente = ""
    for numero, linea in enumerate(texto.splitlines(), start=1):
        for etiqueta in _ETIQUETA.finditer(linea):
            nombre, cadena = etiqueta.group(1), etiqueta.group(2)
            attrs = _atributos(cadena)
            if nombre == "node":
                componente = attrs.get("componentName", "")
                continue
            sensible = attrs.get("type") == "id_Password" or attrs.get("field") in CAMPOS_SENSIBLES
            if not sensible or "value" not in attrs:
                continue
            valor = attrs["value"]
            if es_marcador(valor) or permitido(attrs.get("field", ""), componente, valor):
                continue
            tipo = "password_en_contexto" if nombre == "contextParameter" else "password_en_item"
            yield HallazgoXml(linea=numero, tipo=tipo, valor=valor)
