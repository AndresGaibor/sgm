"""Base de los valores del intérprete: excepción de operadores no soportados y conversión a número.

Movido desde interprete_valores.py sin cambio de comportamiento (hito 242m).
"""

from __future__ import annotations

from sgm.migrar import semantica


class NoSoportadoEnInterprete(RuntimeError):
    """El plan usa algo que el intérprete no sabe ejecutar; se dice qué, no se salta."""

    def __init__(self, kind: str, detalle: str = "") -> None:
        self.kind = kind
        self.detalle = detalle
        super().__init__(f"{kind}: {detalle}" if detalle else kind)


def _numero(valor: object) -> float | None:
    return semantica.como_numero(valor)


def _clave(valor: object) -> tuple:
    """Llave de unión con la comparación de SAS: el faltante es un valor, el texto sin blancos."""
    if semantica.es_faltante(valor):
        return (0, 0.0, "")
    numero = _numero(valor)
    if numero is not None:
        return (1, numero, "")
    return (2, 0.0, semantica.como_texto(valor))


def _nombre_de_columna(filas: list[dict], nombre: object) -> str:
    """Columna que nombra un `ORDER BY` o `DISTINCT`: por nombre o por posición (`ORDER BY 2`)."""
    texto = str(nombre).strip()
    if texto.isdigit() and filas:
        columnas = list(filas[0])
        posicion = int(texto)
        if 1 <= posicion <= len(columnas):
            return columnas[posicion - 1]
    return texto
