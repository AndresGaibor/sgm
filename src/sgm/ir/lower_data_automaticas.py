"""Variables automáticas del DATA step que todavía no se traducen: `_N_` y `_ERROR_` (B-20).

`_N_` es el número de iteración del PDV, que cuenta también las filas que un `WHERE` o un
`IF` filtran. `_ERROR_` marca un error de datos de la fila. Ninguno tiene en el plan un valor
que el Job pueda reproducir todavía, así que una sentencia que los lee sale como operador
`hueco` con su motivo, y no como si fueran columnas: no queda una columna `_n_` inventada ni un
Job que calla la diferencia. La traducción real (un contador antes del filtro) es el resto de B-20.
"""

from __future__ import annotations

import re

_AUTOMATICA = re.compile(r"(?i)(?<![\w'\"])(_n_|_error_)(?![\w'\"])")


def automaticas_en(texto: str) -> list[str]:
    """Nombres de variable automática que lee o escribe el texto, fuera de literales de texto."""
    partes = re.split(r"('[^']*'|\"[^\"]*\")", texto)
    encontradas: list[str] = []
    for k in range(0, len(partes), 2):  # solo los trozos fuera de literales
        encontradas += [m.group(1).lower() for m in _AUTOMATICA.finditer(partes[k])]
    return sorted(set(encontradas))


def motivo(variable: str) -> str:
    codigo = "P-ERROR-AUTOMATICA" if variable == "_error_" else "P-VARIABLE-AUTOMATICA"
    return (
        f"{codigo}: {variable} depende del orden de las filas o de los errores de SAS; el Job no "
        "lo reproduce todavía (sin traducción)"
    )
