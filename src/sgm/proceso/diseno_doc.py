"""Diseño deducido de un programa SAS: las secciones del documento de diseño que ya existen.

Une el linaje, las regiones, las fuentes y salidas, la fontanería y lo declarado en `decisiones/`.
`construir_diseno` devuelve `{codigo_seccion: {clave_de_fila: {columna: texto}}}`, el mismo contrato
que usa la conformidad. `construir_documento` añade el resumen y los pendientes para el Markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sgm.agrupacion import cargar_declaracion
from sgm.flow.model import build_flows
from sgm.flow.regiones import dividir_regiones
from sgm.frontend.program import analyze_program
from sgm.proceso.analisis import analizar_regiones
from sgm.proceso.entradas_salidas import entradas_y_salidas
from sgm.proceso.etapas import Cobertura, cargar_etapas, cobertura
from sgm.proceso.fontaneria import contar_fontaneria, seccion_equivalencias
from sgm.proceso.pendientes import Pendiente, reunir_pendientes
from sgm.proceso.secciones_entrada import cargar_declaradas, seccion_fuentes, seccion_salidas
from sgm.redaction import redact

Diseno = dict[str, dict[str, dict[str, str]]]
SECCIONES_EMITIDAS = ("1.1", "1.4")  # comparables con el diseño manual fila a fila
SECCIONES_GENERICAS = ("6",)  # salen de reglas y hechos; sus claves no coinciden con las del manual


@dataclass
class DocumentoDiseno:
    programa: str
    secciones: Diseno
    pendientes: list[Pendiente]
    resumen: dict[str, int] = field(default_factory=dict)
    etapas: Cobertura | None = None


def construir_documento(
    programa: Path, agrupacion: Path, decisiones_diseno: Path
) -> DocumentoDiseno:
    """Secciones, resumen y pendientes de `programa`, según las decisiones del equipo."""
    texto = programa.read_text(encoding="utf-8", errors="replace")
    modelo = build_flows({programa.name: texto})[programa.name]
    declaracion = cargar_declaracion(agrupacion)
    es = entradas_y_salidas(modelo, declaracion.productos)
    limpio = redact(texto.lstrip("﻿"), programa.name)
    items = analyze_program({programa.name: limpio}, {}).items
    fontaneria = contar_fontaneria(items)
    regiones = analizar_regiones(texto, declaracion)
    etiquetas = [e for r in dividir_regiones(texto, declaracion.marcador) for e in r.etiquetas]
    etapas = cobertura(etiquetas, cargar_etapas(decisiones_diseno))
    secciones: Diseno = {
        "1.1": seccion_fuentes(cargar_declaradas(decisiones_diseno, "fuentes"), es),
        "1.4": seccion_salidas(cargar_declaradas(decisiones_diseno, "salidas"), es),
        "6": seccion_equivalencias(fontaneria),
    }
    resumen = {
        "pasos": len(modelo.steps),
        "regiones": len(regiones.regiones),
        "familias": len(regiones.familias.familias),
        "regiones_sin_copia": len(regiones.familias.unicas),
        "fuentes": len(es.fuentes),
        "persistencias_propias": len(es.persistidas),
        "plantillas_de_salida": len(es.salidas),
        "sentencias_de_fontaneria": sum(e.cantidad for e in fontaneria),
        "etiquetas": etapas.total,
        "etiquetas_con_etapa": sum(etapas.por_etapa.values()),
    }
    return DocumentoDiseno(
        programa.name, secciones, reunir_pendientes(es, regiones, etapas), resumen, etapas
    )


def construir_diseno(programa: Path, agrupacion: Path, decisiones_diseno: Path) -> Diseno:
    """Solo las secciones, con el contrato de la conformidad."""
    return construir_documento(programa, agrupacion, decisiones_diseno).secciones
