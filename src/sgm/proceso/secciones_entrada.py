"""Secciones 1.1 (fuentes externas) y 1.4 (salidas) del documento de diseño.

Cada fila combina lo declarado por el equipo (`decisiones/<programa>.diseno.yaml`, claves `fuentes`
y `salidas`: nombres de parámetros y textos de uso) con lo que el SAS demuestra: si la fuente o la
salida existe en el programa, y con qué ruta o nombre. Lo que el SAS no demuestra queda pendiente.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from sgm.proceso.entradas_salidas import EntradasSalidas, Fuente, nombre_archivo

Fila = dict[str, str]
Seccion = dict[str, Fila]

ESTADO_HALLADA = "Ruta confirmada en SAS"
ESTADO_PENDIENTE = "pendiente"
_TIPO_DE_FUENTE = {
    "excel": "Excel",
    "csv": "CSV",
    "tabla_base": "Tabla Impala",
    "archivo": "Archivo",
}


def cargar_declaradas(path: Path, clave: str) -> list[dict[str, str]]:
    """Lista declarada bajo `clave` en el YAML. Cada elemento necesita su propia `clave`."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    filas: list[dict[str, str]] = []
    vistas: set[str] = set()
    for item in data.get(clave) or []:
        item = {str(k): str(v) for k, v in (item or {}).items()}
        nombre = item.get("clave", "").strip()
        if not nombre:
            raise ValueError(f"{path}: cada elemento de `{clave}` necesita `clave`")
        if nombre in vistas:
            raise ValueError(f"{path}: `{clave}` repite la clave {nombre!r}")
        vistas.add(nombre)
        for campo in ("busca", "equivalente_busca"):
            if campo in item:
                try:
                    re.compile(item[campo])
                except re.error as error:
                    raise ValueError(f"{path}: {nombre!r}: {campo} inválido: {error}") from error
        filas.append(item)
    return filas


def _hallada(busca: str | None, fuentes: list[Fuente]) -> Fuente | None:
    if not busca:
        return None
    patron = re.compile(busca, re.IGNORECASE)
    return next((f for f in fuentes if patron.search(f.ubicacion)), None)


def seccion_fuentes(declaradas: list[dict[str, str]], es: EntradasSalidas) -> Seccion:
    """Sección 1.1: tipo, ubicación, uso y estado de cada fuente declarada."""
    seccion: Seccion = {}
    for d in declaradas:
        hallada = _hallada(d.get("busca"), es.fuentes)
        tipo = d.get("tipo") or (_TIPO_DE_FUENTE[hallada.tipo] if hallada else "pendiente")
        estado = ESTADO_HALLADA if hallada else d.get("estado_sin_hallar", ESTADO_PENDIENTE)
        seccion[d["clave"]] = {
            "tipo": tipo,
            "ubicacion": d.get("ubicacion", "pendiente"),
            "uso": d.get("uso", ""),
            "estado": estado,
        }
    return seccion


def _nombres_de_salidas(es: EntradasSalidas) -> list[str]:
    nombres: list[str] = []
    for plantilla in es.salidas:
        for _producto, ruta in plantilla.instancias:
            nombre = nombre_archivo(ruta)
            if nombre not in nombres:
                nombres.append(nombre)
    return nombres


def seccion_salidas(declaradas: list[dict[str, str]], es: EntradasSalidas) -> Seccion:
    """Sección 1.4: dónde se crea cada salida, su contenido y su equivalente en el SAS."""
    nombres = _nombres_de_salidas(es)
    seccion: Seccion = {}
    for d in declaradas:
        equivalente = d.get("equivalente_sas", "pendiente")
        if busca := d.get("equivalente_busca"):
            patron = re.compile(busca, re.IGNORECASE)
            halladas = [n for n in nombres if patron.search(n)]
            equivalente = ", ".join(halladas) if halladas else "pendiente: el SAS no lo escribe"
        seccion[d["clave"]] = {
            "creado_en": d.get("creado_en", "pendiente"),
            "contenido": d.get("contenido", ""),
            "equivalente_sas": equivalente,
        }
    return seccion
