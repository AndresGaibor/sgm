"""Patrones de fontanería de SAS que no se migran a Talend, como datos.

Fontanería es lo que sirve al propio SAS para orquestar, esperar, medir o limpiar: shell auxiliar,
sondeo de procesos, mensajes, tiempos, variables de control, borrado de temporales, troceo por lotes.
Talend resuelve esas necesidades con otros mecanismos (triggers, tStatCatcher, tDie, Batch size).

Este módulo solo declara los patrones. La pasada `p02_plumbing` los aplica al texto de cada paso y
registra cada coincidencia en `plan.not_migrated` con su equivalente. La clasificación es por FORMA
(qué hace la operación), no por el nombre de la macro que la contiene.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PlumbingPattern:
    category: str
    what: str
    reason: str
    talend: str
    pattern: re.Pattern[str]


PLUMBING_PATTERNS: tuple[PlumbingPattern, ...] = (
    PlumbingPattern(
        "espera",
        "sondeo de procesos con sleep/until del shell",
        "Espera a que terminen procesos del sistema; no transforma datos.",
        "Talend continúa con OnSubjobOk cuando el paso anterior termina.",
        re.compile(r"\b(sleep|until|wait|ps\s+-|while)\b|\bsleep\s*\(", re.IGNORECASE),
    ),
    PlumbingPattern(
        "shell_auxiliar",
        "comando del sistema operativo auxiliar",
        "El comando del shell no transforma filas; solo orquesta el SAS.",
        "tSystem solo si el comando es imprescindible; si no, el orden lo marca el Job.",
        re.compile(r"^\s*(x\s|%sysexec\b|systask\b)", re.IGNORECASE),
    ),
    PlumbingPattern(
        "conexion",
        "apertura o cierre de la sesión con la base de datos",
        "Gestiona la sesión del motor; no transforma datos.",
        "La conexión compartida del Job (tipo Connection) y su cierre los pone la estructura.",
        re.compile(r"^\s*(connect|disconnect)\b", re.IGNORECASE),
    ),
    PlumbingPattern(
        "limpieza_tablas",
        "borrado de una tabla de la base antes de cargar (DROP TABLE)",
        "Elimina la tabla de trabajo para reiniciar la carga; no transforma filas.",
        "La acción de tabla del componente de salida (DROP_CREATE/CLEAR) reemplaza la tabla.",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    ),
    PlumbingPattern(
        "control_macro",
        "bucle o condicional del lenguaje macro (%do, %if, %to)",
        "Controla qué código se genera; no transforma filas.",
        "No hace falta: el orden y las repeticiones los marca el Job.",
        re.compile(r"^\s*%(do|if|to)\b", re.IGNORECASE),
    ),
    PlumbingPattern(
        "mensajes",
        "%put de traza",
        "Escribe en el log; no transforma datos.",
        "tLogRow o los logs de ejecución del Job.",
        re.compile(r"^\s*%put\b", re.IGNORECASE),
    ),
    PlumbingPattern(
        "variables_control",
        "variable de macro calculada en un paso de datos (call symputx)",
        "Pasa un valor a una macro variable de SAS; no transforma filas.",
        "Variable de contexto del Job, o tJava si el valor se calcula en tiempo de ejecución.",
        re.compile(r"\bcall\s+symputx?\s*\(", re.IGNORECASE),
    ),
    PlumbingPattern(
        "medicion",
        "cálculo de la duración del programa (datetime)",
        "Calcula duraciones con datetime(); no transforma datos.",
        "tStatCatcher registra la duración de la ejecución del Job.",
        re.compile(r"\bdatetime\(\)", re.IGNORECASE),
    ),
    PlumbingPattern(
        "troceado_lotes",
        "troceado de un dataset por rangos de observaciones",
        "Reparte la carga en trozos para que el SAS no se quede sin memoria; no es lógica de negocio.",
        "Talend carga el conjunto completo: el componente de salida usa Batch size o escritura por bloques.",
        re.compile(r"\bnlobs\b|\bfirstobs\s*=\s*[&%]|\bobs\s*=\s*[&%]", re.IGNORECASE),
    ),
    PlumbingPattern(
        "conteo",
        "conteo de registros impreso en el log",
        "Solo muestra el número de filas en el log; no transforma datos.",
        "tStatCatcher registra los conteos de filas del Job.",
        re.compile(r"\bselect\s+count\s*\(\s*\*\s*\)\s+into\s*:", re.IGNORECASE),
    ),
)


def match_plumbing(statement: str) -> PlumbingPattern | None:
    """Primer patrón de fontanería que coincide con el texto de un paso, o None."""
    return next((p for p in PLUMBING_PATTERNS if p.pattern.search(statement)), None)
