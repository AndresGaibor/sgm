"""Reglas de variables de contexto Talend a partir de %LET, placeholders y credenciales SAS.

Todo lo que sale de aquí es una propuesta con origen: un valor desconocido queda como `None`
o `needs_value`, nunca se inventa. Las credenciales nunca se copian al plan en claro.
"""

import re
from dataclasses import dataclass, field

SECRET_NAME = re.compile(r"(?i)(pass|pwd|pw|clave|secret|token|key)")
#: Nombres de ambiente del portal y las abreviaturas comunes que los programas usan para ellos.
ENVIRONMENT_ALIASES = {
    "DEV": {"D", "DEV", "DESA", "DES", "DESARROLLO"},
    "QA": {"C", "QA", "CERT", "CERTI", "TEST", "UAT", "PRE"},
    "PROD": {"P", "PROD", "PRO", "PRODUCCION"},
}

PLACEHOLDER = re.compile(r"^\$[A-Za-z_]\w*$")  # %let dataset5 = $dataset5;  (sin resolver)
UNRESOLVED_MACRO = re.compile(r"&[A-Za-z_]\w*")  # referencia a macro variable sin valor
SYSFUNC = re.compile(r"%(?:sysfunc|eval|sysevalf|scan|substr)\b", re.IGNORECASE)
INTEGER = re.compile(r"[+-]?\d+")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{2}[A-Za-z]{3}\d{4}", re.IGNORECASE)
BOOLEAN = {"true", "false", "yes", "no", "y", "n"}

# Rama de un condicional que compara una macro variable con un literal: %if &VAR = LIT %then ...
_BRANCH = re.compile(
    r"(?:%else\s+)?%if\s+&(\w+)\s*(?:eq|=)\s*(\"[^\"]*\"|'[^']*'|[^\s%;]+)\s*%then(.*?)(?=%else|%mend|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_LET = re.compile(r"%let\s+(\w+)\s*=\s*([^;]*);", re.IGNORECASE)

# Credenciales en claro o cifradas en el propio código fuente.
_PASS_LITERAL = re.compile(
    r"""(?i)\b(pass|password|pwd|passwd)\s*=\s*(?:"([^"&][^"]*)"|'([^'&][^']*)')"""
)
_PWENCODE = re.compile(r"(?i)proc\s+pwencode\s+in\s*=\s*(?:\"[^\"]*\"|'[^']*')")


@dataclass
class CredentialHit:
    line: int
    kind: str  # "literal" | "pwencode"


@dataclass
class ContextInfo:
    talend_type: str
    is_secret: bool
    needs_value: bool
    group_values: dict[str, str | None] | None = None
    notes: list[str] = field(default_factory=list)


def is_secret_name(name: str) -> bool:
    return bool(SECRET_NAME.search(name))


def needs_value(value: str | None) -> bool:
    """Valor vacío, placeholder `$nombre` o referencia `&nombre` sin resolver."""
    if value is None or not value.strip():
        return True
    text = value.strip()
    return bool(PLACEHOLDER.match(text) or UNRESOLVED_MACRO.search(text) or SYSFUNC.search(text))


def talend_type(name: str, value: str | None) -> str:
    if is_secret_name(name):
        return "id_Password"
    text = (value or "").strip()
    if text.lower() in BOOLEAN and text:
        return "id_Boolean"
    if text and INTEGER.fullmatch(text):
        return "id_Integer"
    if text and DATE.fullmatch(text):
        return "id_Date"
    return "id_String"


def classify(name: str, value: str | None) -> ContextInfo:
    secret = is_secret_name(name)
    return ContextInfo(
        talend_type=talend_type(name, value),
        is_secret=secret,
        # Un secreto nunca se guarda en el plan: su valor siempre se aporta en el entorno.
        needs_value=secret or needs_value(value),
    )


def credential_hits(source: str | None) -> list[CredentialHit]:
    """Contraseñas literales o cifradas (`pass='...'`, `proc pwencode`). El valor NO se devuelve."""
    if not source:
        return []
    hits: list[CredentialHit] = []
    for match in _PASS_LITERAL.finditer(source):
        hits.append(CredentialHit(line=source.count("\n", 0, match.start()) + 1, kind="literal"))
    for match in _PWENCODE.finditer(source):
        hits.append(CredentialHit(line=source.count("\n", 0, match.start()) + 1, kind="pwencode"))
    return sorted(hits, key=lambda hit: hit.line)


def business_labels(source: str | None) -> list[tuple[int, str]]:
    """Etiquetas de negocio `/* Etiqueta: X */` con su línea, en orden de aparición."""
    if not source:
        return []
    return [
        (source.count("\n", 0, match.start()) + 1, match.group(1).strip().replace("_", " "))
        for match in re.finditer(r"/\*\s*Etiqueta:\s*(.*?)\s*\*/", source)
    ]


def label_for_line(labels: list[tuple[int, str]], line: int) -> str | None:
    """Etiqueta más cercana por encima de `line` (None si no hay ninguna)."""
    found = None
    for label_line, text in labels:
        if label_line > line:
            break
        found = text
    return found


def environment_name(literal: str) -> str:
    """Nombre de ambiente del portal para un literal del programa (`DESA` -> DEV). Sin alias: el propio literal."""
    text = literal.strip().strip("'\"").upper()
    for name, aliases in ENVIRONMENT_ALIASES.items():
        if text in aliases:
            return name
    return text


def environment_chains(source: str | None) -> dict[str, dict[str, dict[str, str]]]:
    """Cadenas de ambiente: por cada macro variable que un condicional compara con al menos dos literales
    distintos, {literal: {variable asignada: valor}} con las asignaciones `%let` de cada rama.
    El nombre de la variable no importa: la estructura es la que define el cambio de ambiente."""
    if not source:
        return {}
    chains: dict[str, dict[str, dict[str, str]]] = {}
    for match in _BRANCH.finditer(source):
        compared, literal = match.group(1).casefold(), match.group(2).strip().strip("'\"")
        branch = {a.group(1): a.group(2).strip() for a in _LET.finditer(match.group(3))}
        chains.setdefault(compared, {}).setdefault(literal, {}).update(branch)
    return {compared: branches for compared, branches in chains.items() if len(branches) >= 2}


def environment_groups(source: str | None) -> dict[str, dict[str, str]]:
    """Grupos de contexto por ambiente: cada variable que cambia entre ramas (y la variable que decide el
    ambiente, con su literal), como {variable: {DEV: valor, QA: valor, PROD: valor}}."""
    groups: dict[str, dict[str, str]] = {}
    for compared, branches in environment_chains(source).items():
        assigned: dict[str, dict[str, str]] = {}
        for literal, values in branches.items():
            for name, value in values.items():
                assigned.setdefault(name, {})[environment_name(literal)] = value
        for name, by_env in assigned.items():
            if len(by_env) >= 2:
                groups.setdefault(name, {}).update(by_env)
        groups.setdefault(compared, {}).update({environment_name(lit): lit for lit in branches})
    return groups


def environment_parameters(source: str | None) -> list[str]:
    """Macro variables que deciden el ambiente (las que un condicional compara con literales distintos)."""
    return sorted(environment_chains(source))


def env_group(values: dict[str, str]) -> dict[str, str | None]:
    """Valores por ambiente: DEV, QA y PROD siempre; otros nombres de ambiente del programa se conservan."""
    group: dict[str, str | None] = {"DEV": None, "QA": None, "PROD": None}
    group.update(values)
    return group
