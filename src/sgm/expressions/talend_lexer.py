"""Tokenización de expresiones SAS y formatos literales."""

import re

from sgm.expressions.talend_core import Unsupported

_TOKEN = re.compile(
    r"""\s*(?:
    (?P<datelit>'[0-9]{1,2}[A-Za-z]{3}[0-9]{2,4}'[dD])
    |(?P<name>(?:[A-Za-z_]\w*\.)?'[^']+'[nN])
    |(?P<str>'(?:[^']|'')*'|"(?:[^"]|"")*")
    |(?P<fmt>(?:\$?[A-Za-z_][A-Za-z_0-9]*\.\d*|\$\d+\.\d*)(?![\w]))
    |(?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)
    |(?P<mvar>&+[A-Za-z_]\w*\.?)
    |(?P<op>\*\*|\^=|~=|¬=|<>|>=|<=|\|\||!!|=|>|<|\+|-|\*|/|\(|\)|,|&|\||\^|~|¬|\.)
    |(?P<id>[A-Za-z_À-ɏ][\wÀ-ɏ]*(?:\.[A-Za-z_À-ɏ][\wÀ-ɏ]*)?)
    )""",
    re.VERBOSE,
)


def _tokens(text: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise Unsupported("token no soportado en la expresión; queda pendiente de revisión")
        out.append((m.lastgroup or "", m.group(m.lastgroup or "")))
        pos = m.end()
    return out


def _collapse_whitespace_outside_strings(text: str) -> str:
    """Normaliza espacios SAS sin alterar el contenido de literales entre comillas."""
    out: list[str] = []
    quote: str | None = None
    pending_space = False
    pos = 0
    while pos < len(text):
        char = text[pos]
        if quote is not None:
            out.append(char)
            if char == quote:
                if pos + 1 < len(text) and text[pos + 1] == quote:
                    out.append(text[pos + 1])
                    pos += 2
                    continue
                quote = None
            pos += 1
            continue
        if char in ("'", '"'):
            if pending_space and out:
                out.append(" ")
            pending_space = False
            quote = char
            out.append(char)
        elif char.isspace():
            pending_space = bool(out)
        else:
            if pending_space and out:
                out.append(" ")
            pending_space = False
            out.append(char)
        pos += 1
    return "".join(out).strip()


def _clean(text: str) -> str:
    """Quita lo que acompaña a una expresión de PROC SQL y no es parte de ella."""
    text = _collapse_whitespace_outside_strings(text)
    text = re.sub(r"(?i)^(on|where|having)\s+", "", text)
    text = re.sub(r"(?i)^distinct\s+", "", text)
    text = re.sub(
        r"(?i)\s+(label|format|informat|length)\s*=\s*(\"[^\"]*\"|'[^']*'|\S+)\s*$", "", text
    )
    text = re.sub(r"(?i)\s+as\s+\w+\s*$", "", text)
    return text.strip()
