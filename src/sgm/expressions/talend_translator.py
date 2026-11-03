"""Traductor de expresiones SAS a lo que Talend trae de fábrica (fachada pública).

La lógica está en `talend_base`, `talend_parser` y `talend_funciones`. Desde aquí se expone
`translate_to_talend`, con `Unsupported` y `Result`.
"""

import re

from sgm.expressions.talend_base import (
    Result,
    Unsupported,
    _tokens,
)
from sgm.expressions.talend_funciones import (
    _clean,
)
from sgm.expressions.talend_parser import (
    _P,
)


def translate_to_talend(sas: str, entrada: str = "input_row") -> Result:
    """Traduce una expresión SAS a Java con rutinas de Talend; `Unsupported` si no hay traducción segura.

    `entrada` es el nombre de la variable de la conexión de entrada del tMap (`row1`, `row_origen_a_map`...). En Studio
    no existe `input_row`: el llamador pasa el nombre real.
    """
    text = _clean(sas)
    if not text:
        raise Unsupported("expresión vacía")
    if not re.fullmatch(r"[A-Za-z_]\w*", entrada):
        raise Unsupported(f"nombre de conexión no válido: {entrada!r}")
    parser = _P(_tokens(text), entrada)
    result = parser.expr()
    if parser.i != len(parser.t):
        raise Unsupported(f"texto sobrante: {parser.peek()[1]!r}")
    return Result(
        result.java,
        sorted(set(parser.cols)),
        sorted(parser.warnings),
        result.kind,
        sorted(parser.functions),
    )
