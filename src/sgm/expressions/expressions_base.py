"""Base de las expresiones SAS: resultado, excepción y tokens (sin funciones ni parser)."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FUNCTIONS_DIR = Path(__file__).resolve().parents[3] / "rules" / "sas" / "functions"


def _plantillas() -> tuple[dict[str, str], dict[str, str]]:
    """Plantillas Java de las funciones simples y su aviso, leídas de `rules/sas/functions/`."""
    plantillas: dict[str, str] = {}
    avisos: dict[str, str] = {}
    for path in sorted(FUNCTIONS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if "java" in data:
            plantillas[data["sas"]] = data["java"]
            avisos[data["sas"]] = data.get("warning", "")
    return plantillas, avisos


@dataclass
class Translation:
    sas: str
    talend: str | None = None
    columns: list[str] = field(default_factory=list)
    simple: list[dict] | None = None  # condiciones tFilterRow (modo simple)
    logical: str | None = None  # "&&" | "||" para el modo simple
    warnings: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)  # llamadas SAS encontradas por el parser
    engine: str = (
        "inline"  # "inline" (traductor original) | "talend" (rutinas de sistema de Talend)
    )
    kind: str = "any"  # num | str | bool | date | any: tipo que el Java emitido produce


class _Unsupported(Exception):
    pass


_TOKEN = re.compile(
    r"""\s*(?:
    (?P<str>'(?:[^']|'')*'|"(?:[^"]|"")*")
    |(?P<num>\d+(?:\.\d+)?)
    |(?P<mvar>&[A-Za-z_]\w*\.?)
    |(?P<op>\^=|~=|<>|>=|<=|\|\||=|>|<|\+|-|\*|/|\(|\)|,|&|\|)
    |(?P<fmt>(?:best|comma|dollar|yymmdd|ddmmyy|mmddyy|date|datetime)\d*\.\d*)
    |(?P<id>[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)?)
    )""",
    re.VERBOSE,
)
_ARITHMETIC_TOKEN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|[()+*/-]"
)
_CMP = {"=": "==", "eq": "==", "^=": "!=", "~=": "!=", "<>": "!=", "ne": "!=", ">": ">", "gt": ">",
        "<": "<", "lt": "<", ">=": ">=", "ge": ">=", "<=": "<=", "le": "<="}  # fmt: skip
# Funciones de una línea (`rules/sas/functions/`, F1.4): plantilla Java y aviso de nulos.
_FUNCS, _FUNCS_AVISO = _plantillas()


_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
