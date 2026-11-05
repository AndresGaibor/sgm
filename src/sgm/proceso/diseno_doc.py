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
from sgm.flow.regiones import asignar_regiones, dividir_regiones
from sgm.frontend.program import analyze_program
from sgm.proceso.analisis import analizar_regiones
from sgm.proceso.colapso import colapsar, plantilla_por_etapa
from sgm.proceso.entradas_salidas import entradas_y_salidas
from sgm.proceso.etapas import Cobertura, cargar_etapas, cobertura, etapa_de
from sgm.proceso.fontaneria import contar_fontaneria, seccion_equivalencias
from sgm.proceso.pendientes import Pendiente, reunir_pendientes
from sgm.proceso.secciones_decisiones import cargar_decisiones, seccion_decisiones
from sgm.proceso.secciones_entrada import (
    ORIGEN_DECLARADA,
    cargar_declaradas,
    origen_fuentes,
    origen_salidas,
    seccion_fuentes,
    seccion_salidas,
)
from sgm.proceso.secciones_intercambio import seccion_intercambio, seccion_periodo
from sgm.proceso.secciones_jobs import componentes_emitidos, seccion_jobs
from sgm.proceso.secciones_parametros import seccion_parametros
from sgm.redaction import redact
from sgm.talend_item.arquitectura import cargar_arquitectura

Diseno = dict[str, dict[str, dict[str, str]]]
# Comparables con el diseño manual fila a fila (la conformidad los evalúa).
SECCIONES_EMITIDAS = ("1.1", "1.2", "1.3", "1.4", "2.1")
# Sin comparación fila a fila: salen de hechos y reglas, o sus claves no son las del manual.
SECCIONES_GENERICAS = ("3", "5", "6")


@dataclass
class DocumentoDiseno:
    programa: str
    secciones: Diseno
    pendientes: list[Pendiente]
    resumen: dict[str, int] = field(default_factory=dict)
    etapas: Cobertura | None = None
    # Origen de cada fila de las secciones emitidas: `sas` o `declarada` (la conformidad lo usa).
    origenes: dict[str, dict[str, str]] = field(default_factory=dict)


def _jobs_yaml(programa: Path, decisiones_diseno: Path) -> Path:
    """Ruta de `<programa>.jobs.yaml`, junto a las decisiones de diseño."""
    return decisiones_diseno.with_name(f"{programa.stem}.jobs.yaml")


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
    declaradas = cargar_etapas(decisiones_diseno)
    etapas = cobertura(etiquetas, declaradas)
    colapso = colapsar(
        modelo,
        asignar_regiones(modelo, regiones.regiones),
        lambda paso: etapa_de(paso.label, declaradas) if paso.label else None,
    )
    familias = [tuple(i.region for i in f.instancias) for f in regiones.familias.familias]
    eliminadas = frozenset(e.nombre for e in declaradas if e.elimina)
    bloques = plantilla_por_etapa(colapso, familias, list(regiones.familias.unicas), eliminadas)
    fuentes = cargar_declaradas(decisiones_diseno, "fuentes")
    salidas = cargar_declaradas(decisiones_diseno, "salidas")
    parametros, origen_parametros = seccion_parametros(
        cargar_declaradas(decisiones_diseno, "parametros"), es
    )
    decisiones = cargar_decisiones(decisiones_diseno.with_name(f"{programa.stem}.decisiones.yaml"))
    origen_1_1 = origen_fuentes(fuentes, es)
    intercambio, origen_intercambio = seccion_intercambio(
        cargar_declaradas(decisiones_diseno, "intercambios")
    )
    jobs_yaml = _jobs_yaml(programa, decisiones_diseno)
    arq = cargar_arquitectura(jobs_yaml) if jobs_yaml.is_file() else None
    fecha = arq.periodo if arq else None
    origen_fecha = origen_1_1.get(fecha.fuente, ORIGEN_DECLARADA) if fecha else ""
    periodo, origen_periodo = seccion_periodo(arq, origen_fecha)
    conteo = componentes_emitidos(programa, agrupacion, decisiones_diseno, jobs_yaml) if arq else {}
    secciones: Diseno = {
        "1.1": seccion_fuentes(fuentes, es),
        "1.2": intercambio,
        "1.3": periodo,
        "1.4": seccion_salidas(salidas, es),
        "2.1": parametros,
        "3": seccion_jobs(conteo),
        "5": seccion_decisiones(decisiones),
        "6": seccion_equivalencias(fontaneria),
    }
    origenes = {
        "1.1": origen_1_1,
        "1.2": origen_intercambio,
        "1.3": origen_periodo,
        "1.4": origen_salidas(salidas, es),
        "2.1": origen_parametros,
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
        "pasos_de_datos": colapso.pasos_de_datos,
        "bloques_sin_parametrizar": colapso.bloques,
        "bloques_en_plantillas": sum(bloques.values()),
    }
    return DocumentoDiseno(
        programa.name, secciones, reunir_pendientes(es, regiones, etapas), resumen, etapas, origenes
    )


def construir_diseno(programa: Path, agrupacion: Path, decisiones_diseno: Path) -> Diseno:
    """Solo las secciones, con el contrato de la conformidad."""
    return construir_documento(programa, agrupacion, decisiones_diseno).secciones
