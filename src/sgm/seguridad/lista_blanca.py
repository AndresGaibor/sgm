"""Lista blanca de valores de contraseña que el escáner acepta a propósito.

Es la única excepción a la regla "PASSWORD con valor es un hallazgo". Cada entrada nombra el campo,
el componente que la contiene, el valor literal tal como sale en el `.item` y el motivo. Para
auditarla: `grep -n Excepcion src/sgm/seguridad/lista_blanca.py`. La prueba
`tests/unit/test_secretos_limpios.py` comprueba que el emisor la usa y que, sin ella, el escáner
da hallazgos. Añadir una entrada exige revisión de Seguridad (ver docs/secretos.md).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Excepcion:
    campo: str  # atributo `field` del elementParameter
    componente: str  # `componentName` del nodo que contiene el parámetro
    valor: str  # valor tal como sale en el `.item`, sin escapar XML y con sus comillas
    motivo: str


LISTA_BLANCA: tuple[Excepcion, ...] = (
    Excepcion(
        campo="PASSWORD",
        componente="tFileInputExcel",
        valor='"sgm_ref"',
        motivo=(
            "Marcador sintético. tFileInputExcel no compila con PASSWORD vacío ni con '***', y "
            "el Excel de insumo no tiene clave. Lo emiten flujos_ubicacion, periodo y "
            "totalizadores. No es una contraseña."
        ),
    ),
)


def valor_permitido_en_texto(valor: str) -> bool:
    """Valor de la lista blanca fuera de un `.item`, p. ej. una cita en un documento del repo."""
    return any(e.valor == valor for e in LISTA_BLANCA)


def permitido(campo: str, componente: str, valor: str) -> bool:
    """Indica si un parámetro PASSWORD con ese valor está en la lista blanca."""
    return any(
        e.campo == campo and e.componente == componente and e.valor == valor for e in LISTA_BLANCA
    )
