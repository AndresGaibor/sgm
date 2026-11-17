"""PROC FORMAT VALUE discreto; los rangos y opciones siguen pendientes para D1."""

from __future__ import annotations

import re

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder
from sgm.ir.formatos_usuario import FormatoUsuario
from sgm.ir.lower_procs_common import unsupported
from sgm.ir.models import Evidence

_LITERAL = r"(?:'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\")"
_PAIR = re.compile(rf"\s*({_LITERAL}|OTHER)\s*=\s*({_LITERAL})(?=\s|$)", re.I)
_VALUE = re.compile(r"VALUE\s+(\$?[A-Za-z_]\w*)\s+(.+)", re.I | re.S)


def _literal(text: str) -> str:
    return text[1:-1].replace(text[0] * 2, text[0])


def lower_format(step: Proc, ev: Evidence, b: Builder) -> list[FormatoUsuario]:
    """Registra solo declaraciones completas demostradas (proc.pdf, pp. 1173–1181)."""
    formats = []
    code = "P-FORMATO-SIN-SOPORTE"
    valid = bool(step.body) and not step.options and not step.flags
    for statement in step.body:
        match = _VALUE.fullmatch(statement.strip())
        if match is None:
            valid = False
            break
        name, body = match.groups()
        if re.match(r"\s*[-+]?\d+(?:\.\d+)?\s*-\s*[-+]?\d+(?:\.\d+)?\s*=", body):
            code = "P-FORMATO-RANGO-SIN-SOPORTE"
            valid = False
            break
        if not name.startswith("$") or name[-1].isdigit():
            valid = False
            break
        pairs, other, position = [], None, 0
        while position < len(body):
            pair = _PAIR.match(body, position)
            if pair is None:
                valid = False
                break
            key, label = pair.groups()
            if key.upper() == "OTHER":
                if other is not None:
                    valid = False
                    break
                other = _literal(label)
            else:
                key = _literal(key)
                if any(previous == key for previous, _ in pairs):
                    valid = False
                    break
                pairs.append((key, _literal(label)))
            position = pair.end()
        if not valid:
            break
        formats.append(FormatoUsuario(name.lower(), tuple(pairs), other))
    names = [fmt.nombre for fmt in [*b.formatos, *formats]]
    if len(names) != len(set(names)):
        valid = False
    if not valid:
        unsupported(step, ev, b, f"Pendiente: {code}; PROC FORMAT fuera del mapa discreto "
                    "de carácter documentado en proc.pdf, pp. 1173, 1178 y 1181",
                    pending_code=code)
        return []
    return formats
