"""Traductor de expresiones SAS a lo que Talend trae de fábrica, sin bibliotecas propias.

Talend guarda una expresión como Java dentro de `tMap` o del modo avanzado de `tFilterRow`. Este traductor emite solo:

- **Rutinas de sistema de Talend** disponibles en cualquier proyecto (`StringHandling`, `TalendDate`, `Mathematical`,
  `Relational`), con firmas leídas de la instalación de Studio 8.0.
- **Java nativo** (`Math`, `Objects`, `Number`, operadores) con las guardas de nulo necesarias.

No hay nada que instalar. El **valor perdido de SAS es `null`**: los operadores lo propagan como SAS (un perdido numérico es
menor que cualquier número; `a + .` es perdido). Lo que SAS hace distinto y Talend no tiene (`lag`, `retain`) lanza
`Unsupported` y queda como pendiente. Cuando el tipo de una columna no se conoce, solo se emiten comparaciones que no lo
necesitan (igualdad con un literal, nulos, `Comparable`); los cálculos exactos esperan al esquema.
"""

import re

from sgm.expressions.talend_core import E, Result, Unsupported
from sgm.expressions.talend_functions import _FUNCTIONS
from sgm.expressions.talend_lexer import _clean, _tokens
from sgm.expressions.talend_parser import ExpressionParser

__all__ = ["E", "Result", "Unsupported", "translate_to_talend"]


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
    parser = ExpressionParser(_tokens(text), entrada, _FUNCTIONS)
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
