"""Traducción conservadora de condiciones y expresiones SAS a Java (fachada pública).

La lógica está en `expressions_base`, `expressions_funciones` y `expressions_parser`. Desde
aquí se expone `translate`.
"""

import os
import re

from sgm.expressions.expressions_base import (
    _ARITHMETIC_TOKEN,
    Translation,
    _Unsupported,
)
from sgm.expressions.expressions_parser import (
    _Parser,
    _tokens,
)
from sgm.expressions.talend_lexer import _collapse_whitespace_outside_strings
from sgm.expressions.talend_translator import (
    Unsupported,
    translate_to_talend,
)


def talend_expressions_enabled() -> bool:
    """Interruptor del traductor con rutinas de Talend, activo por defecto.

    Se puede apagar con `SGM_TALEND_EXPRESSIONS=0`. Las expresiones nuevas quedan parciales y requieren
    revisión hasta comprobar en Studio que el Java que emiten compila (`talend_job_verify`).
    """
    return os.environ.get("SGM_TALEND_EXPRESSIONS", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def translate(sas: str) -> Translation:
    """Traduce una condición o expresión SAS; `talend=None` si no es seguro.

    Primero el traductor en línea (lo que ya traducía no cambia); si se rinde y `SGM_TALEND_EXPRESSIONS` está activo, el de rutinas de Talend, que cubre la
    gramática completa con `StringHandling`, `TalendDate`, `Mathematical` y Java nativo, y conserva la semántica del perdido.
    """
    t = _translate_inline(sas)
    if t.talend is not None:
        # El tipo del resultado no depende del motor que escribe el Java: el traductor completo lo sabe.
        t.kind = _talend_kind(sas)
        return t
    if not talend_expressions_enabled():
        return t
    try:
        result = translate_to_talend(sas)
    except Unsupported as error:
        t.warnings.append(f"Sin traducción con rutinas de Talend: {error}")
        return t
    t.talend, t.columns, t.warnings, t.functions, t.engine = (
        result.java,
        result.columns,
        result.warnings,
        result.functions,
        "talend",
    )
    t.kind = result.kind
    return t


def _talend_kind(sas: str) -> str:
    """Tipo del valor que produce la expresión, según el traductor completo (`any` si no lo sabe)."""
    try:
        return translate_to_talend(sas).kind
    except Unsupported:
        return "any"


def _translate_inline(sas: str) -> Translation:
    t = Translation(sas=sas)
    s = _collapse_whitespace_outside_strings(sas)
    if re.search(r"\bis\s+(not\s+)?missing\b|\bcalculated\b", s, re.IGNORECASE):
        t.warnings.append("Construcción SAS sin traducción automática")
        return t
    try:
        p = _Parser(_tokens(s))
        java = p.expr()
        if p.i != len(p.t):
            raise _Unsupported("texto sobrante")
    except _Unsupported:
        t.warnings.append(
            "Sin traducción automática: expresión no admitida; queda pendiente de revisión"
        )
        return t
    t.talend = None if p.unsafe_comparison else java
    t.columns = sorted(set(p.cols))
    t.warnings = sorted(set(p.warnings))
    if p.simple and all(p.simple) and len(p.ops) <= 1 and p.ops <= {"&&", "||"}:
        t.simple = p.simple
        t.logical = next(iter(p.ops), "&&")
    return t


def is_simple_arithmetic_translation(expression: str | None) -> bool:
    """Indica si la traducción solo contiene columnas, números y aritmética básica."""
    if not expression:
        return False
    tokens = _ARITHMETIC_TOKEN.findall(expression)
    if not tokens or "".join(tokens) != re.sub(r"\s+", "", expression):
        return False

    expecting_value = True
    depth = 0
    for token in tokens:
        if token == "(":
            if not expecting_value:
                return False
            depth += 1
            continue
        if token == ")":
            if expecting_value or depth == 0:
                return False
            depth -= 1
            expecting_value = False
            continue
        if token in {"+", "-", "*", "/"}:
            if token in {"+", "-"} and expecting_value:
                continue
            if expecting_value:
                return False
            expecting_value = True
            continue
        if not expecting_value:
            return False
        expecting_value = False
    return not expecting_value and depth == 0
