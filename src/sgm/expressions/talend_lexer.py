"""Tokenización de expresiones SAS y formatos literales."""

import re

from sgm.expressions.talend_core import Unsupported

_TOKEN = re.compile(
    r"""\s*(?:
    (?P<datelit>'[0-9]{1,2}[A-Za-z]{3}[0-9]{2,4}'[dD])
    |(?P<name>(?:[A-Za-z_]\w*\.)?'[^']+'[nN])
    |(?P<str>'(?:[^']|'')*'|"(?:[^"]|"")*")
    |(?P<fmt>(?:\$?[A-Za-z_]+\d*\.\d*|\$\d+\.\d*)(?![\w]))
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
            raise Unsupported(f"token no soportado: {text[pos : pos + 12]!r}")
        out.append((m.lastgroup or "", m.group(m.lastgroup or "")))
        pos = m.end()
    return out


def _clean(text: str) -> str:
    """Quita lo que acompaña a una expresión de PROC SQL y no es parte de ella."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?i)^(on|where|having)\s+", "", text)
    text = re.sub(r"(?i)^distinct\s+", "", text)
    text = re.sub(
        r"(?i)\s+(label|format|informat|length)\s*=\s*(\"[^\"]*\"|'[^']*'|\S+)\s*$", "", text
    )
    text = re.sub(r"(?i)\s+as\s+\w+\s*$", "", text)
    return text.strip()
