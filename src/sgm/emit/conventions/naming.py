"""Reglas de nombres para Jobs y carpetas de Talend.

Porte de la versión anterior: se conservan validación de nombres, plantillas y render. Se quitó la
vista previa de renombrado masivo, que dependía del modelo de plan anterior.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

DEFAULT_NAME_TEMPLATE = "job_{programa}"
TEMPLATE_TOKENS = ("proyecto", "carpeta", "programa")
MAX_JOB_NAME = 60
RESERVED_FOLDERS = frozenset(
    {"tests", "target", "src"}
)  # nombres que Git no admite en el repositorio


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def validate_job_name(
    name: str, *, taken: set[str] | frozenset[str] | list[str] = ()
) -> str | None:
    """Mensaje de error si el nombre no sirve para un Job; None si es válido."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return "El nombre debe empezar con una letra o guion bajo y usar solo letras, números y guion bajo."
    if len(name) > MAX_JOB_NAME:
        return "El nombre no puede pasar de 60 caracteres."
    if name.casefold() in {item.casefold() for item in taken}:
        return "Ya existe otro Job con ese nombre."
    return None


def validate_template(template: str) -> str | None:
    tokens = re.findall(r"\{([^{}]+)\}", template)
    for token in tokens:
        if token not in TEMPLATE_TOKENS:
            return f"Token desconocido: {{{token}}}."
    if "{programa}" not in template:
        return "La plantilla debe incluir {programa}."
    return None


def render_job_name(template: str, *, project: str, program: str, depth: int = 0) -> str:
    parts = PurePosixPath(program.replace("\\", "/")).parts
    stem = PurePosixPath(parts[-1]).stem if parts else ""
    prefix = parts[max(0, len(parts) - depth - 1) : -1] if depth else []
    program_name = slug("_".join([*prefix, stem]))
    folder = slug(parts[-2]) if len(parts) > 1 else ""
    rendered = template.replace("{proyecto}", slug(project))
    rendered = rendered.replace("{carpeta}", folder).replace("{programa}", program_name)
    rendered = re.sub(r"[^A-Za-z0-9_]+", "_", rendered)
    rendered = re.sub(r"_+", "_", rendered).strip("_")
    if not rendered or rendered[0].isdigit():
        rendered = f"job_{rendered}"
    return rendered
