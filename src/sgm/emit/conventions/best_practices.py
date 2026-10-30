"""Buenas prácticas de Talend comprobables sobre la especificación de un Job.

Son recomendaciones: no cambian nada. Cada regla tiene un identificador estable (BP-*). Porte de la
versión anterior sin las dependencias del servidor MCP: la entrada es un dict plano con `jobName`,
`folderPath`, `components` y `connections`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from sgm.emit.conventions.infra import (
    DATABASE_ACCESS,
    DATABASE_CONNECTION,
    MAX_COMPONENTS_PER_JOB,
)

RESERVED_GIT_NAMES = frozenset({"tests", "target", "src"})
JOB_PREFIX = "job_"

_ENVIRONMENT_PARAMETERS = ("FILENAME", "DIRECTORY", "HOST", "PORT", "DBNAME", "URL")
_PASSWORD_PARAMETERS = ("PASS", "PASSWORD", "PASSPHRASE")
_CONTEXT_REFERENCE = re.compile(r"\bcontext\.\w+")
_ERROR_COMPONENTS = frozenset(
    {"tDie", "tWarn", "tLogCatcher", "tStatCatcher", "tFlowMeterCatcher", "tAssertCatcher"}
)
_ERROR_CONNECTORS = frozenset({"SUBJOB_ERROR", "COMPONENT_ERROR", "REJECT"})


@dataclass(frozen=True)
class PracticeFinding:
    rule: str
    severity: Literal["error", "warning", "info"]
    message: str
    component: str | None = None
    parameter: str | None = None


def _is_literal(value: Any) -> bool:
    """Valor fijo en el Job: no vacío, no cifrado (`enc:`) ni una referencia a contexto."""
    text = str(value).strip() if value is not None else ""
    return bool(text) and not text.startswith("enc:") and not _CONTEXT_REFERENCE.search(text)


def check_job_arguments(arguments: dict[str, Any]) -> list[PracticeFinding]:
    """Revisa la especificación de un Job (sin sus hijos)."""
    components = [item for item in arguments.get("components", []) if isinstance(item, dict)]
    connections = [item for item in arguments.get("connections", []) if isinstance(item, dict)]
    findings: list[PracticeFinding] = []

    job_name = str(arguments.get("jobName") or "")
    if job_name and not job_name.startswith(JOB_PREFIX):
        findings.append(
            PracticeFinding(
                rule="BP-NAME-01",
                severity="info",
                message=f"El Job '{job_name}' no empieza por '{JOB_PREFIX}'; la guía de Talend propone ese prefijo para distinguir Jobs de rutas, servicios y tareas.",
            )
        )
    folders = [
        part
        for part in str(arguments.get("folderPath") or "").replace("\\", "/").split("/")
        if part
    ]
    reserved = [name for name in [job_name, *folders] if name.lower() in RESERVED_GIT_NAMES]
    if reserved:
        findings.append(
            PracticeFinding(
                rule="BP-NAME-02",
                severity="warning",
                message=f"El nombre '{reserved[0]}' está reservado con Git (tests, target, src): los cambios del Job no se suben al repositorio; renómbralo.",
            )
        )

    for component in components:
        unique_name = component.get("uniqueName")
        parameters = component.get("parameters") or {}
        for name in _ENVIRONMENT_PARAMETERS:
            if _is_literal(parameters.get(name)):
                findings.append(
                    PracticeFinding(
                        rule="BP-CTX-01",
                        severity="warning",
                        component=unique_name,
                        parameter=name,
                        message=f"{unique_name}: {name} tiene un valor fijo; usa una variable de contexto para cambiar de entorno sin editar el Job.",
                    )
                )
        for name in _PASSWORD_PARAMETERS:
            if _is_literal(parameters.get(name)):
                findings.append(
                    PracticeFinding(
                        rule="BP-SEC-01",
                        severity="error",
                        component=unique_name,
                        parameter=name,
                        message=f"{unique_name}: {name} contiene una contraseña en claro; guárdala en una variable de contexto de tipo contraseña.",
                    )
                )

    names = [str(item.get("componentName", "")) for item in components]
    has_connection = any(DATABASE_CONNECTION.match(name) for name in names)
    database_access = [name for name in names if DATABASE_ACCESS.match(name)]
    if len(database_access) >= 2 and not has_connection:
        findings.append(
            PracticeFinding(
                rule="BP-DB-01",
                severity="warning",
                message=f"El Job abre {len(database_access)} accesos a base de datos sin una conexión compartida; usa un componente de conexión con commit y cierre.",
            )
        )

    handles_errors = any(name in _ERROR_COMPONENTS for name in names) or any(
        item.get("connectorName") in _ERROR_CONNECTORS for item in connections
    )
    if len(components) >= 2 and not handles_errors:
        findings.append(
            PracticeFinding(
                rule="BP-ERR-01",
                severity="info",
                message="El Job no tiene manejo de errores (tDie, tWarn, tLogCatcher o una conexión de error); un fallo pasaría sin registro.",
            )
        )

    if len(components) > MAX_COMPONENTS_PER_JOB:
        findings.append(
            PracticeFinding(
                rule="BP-SIZE-01",
                severity="warning",
                message=f"El Job tiene {len(components)} componentes (máximo recomendado {MAX_COMPONENTS_PER_JOB}); divídelo en Jobs hijo con tRunJob.",
            )
        )
    return findings
