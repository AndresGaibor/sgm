"""Esquemas y tablas fijas de los casos L2 y L3 (JOIN y agregados).

Las tablas de búsqueda (homologación, zonas, metas, canales válidos) son fijas y se escriben a mano:
así un código repetido en la búsqueda es un hecho del caso y no un accidente del azar. Las tablas de
hechos (operaciones, facturas, cuentas) son aleatorias con semilla fija. Todo es ficticio.
"""

from __future__ import annotations

from dataclasses import dataclass

from .datos_ficticios import CANALES, Entrada, col

TIPOS_OPERACION = ("CC", "TI", "CE", "PA", "NIT", "PP")
# CC aparece dos veces en la lista: sale con más frecuencia (para casos que necesitan CC presente).
TIPOS_CON_CC_FRECUENTE = ("CC", "CC", "TI", "PA", "NIT", "PP", "CE")


@dataclass(frozen=True)
class Fija:
    """Tabla con filas escritas a mano: encabezado y filas de texto, en el orden dado."""

    encabezado: tuple[str, ...]
    filas: tuple[tuple[str, ...], ...]


def operaciones(
    n: int,
    *,
    vacios_tipo: int = 0,
    vacios_monto: int = 0,
    tipos: tuple[str, ...] = TIPOS_OPERACION,
) -> Entrada:
    """Operaciones con tipo de documento. `NIT` y `PP` no están en la homologación: son inválidas.

    `tipos` permite cambiar la frecuencia de los códigos (por ejemplo, para asegurar que hay CC).
    """
    return Entrada(
        n,
        (
            col("id_operacion", "secuencia", 1),
            col("tipo_doc", "elige", tipos, vacios=vacios_tipo),
            col("id_cliente", "entero", 101, 110),
            col("monto", "entero", 50, 900, vacios=vacios_monto),
            col("canal", "elige", CANALES),
        ),
    )


def facturas(n: int) -> Entrada:
    """Facturas con importe decimal de dos cifras, para las sumas con coma flotante."""
    return Entrada(
        n,
        (
            col("id_factura", "secuencia", 1),
            col("canal", "elige", CANALES),
            col("importe", "decimal", 10, 900),
        ),
    )


def columnas_depositos(n: int, *, vacios: int = 0) -> Entrada:
    """Cuentas de depósito con el saldo como texto con blancos (origen de un DATA step)."""
    return Entrada(
        n,
        (
            col("id_cuenta", "secuencia", 5001),
            col("tipo_cta", "elige", ("AHORROS", "CORRIENTE")),
            col("fin_saldo_cta", "texto_blancos", 0, 5000, vacios=vacios),
        ),
    )


# Los códigos RC y PE no aparecen en los datos: están en el catálogo para tener más filas, y no
# cambian ningún resultado.
HOMOLOGACION_TPO_DOC = Fija(
    ("CNAME", "DESCRIPCION"),
    (
        ("CC", "Cédula de ciudadanía"),
        ("TI", "Tarjeta de identidad"),
        ("CE", "Cédula de extranjería"),
        ("PA", "Pasaporte"),
        ("RC", "Registro civil"),
        ("PE", "Permiso especial de permanencia"),
    ),
)

# Mismo catálogo con 'CC' repetido: cada operación con ese código aparece dos veces al unir.
HOMOLOGACION_DUP = Fija(
    ("CNAME", "DESCRIPCION"),
    (
        ("CC", "Cédula de ciudadanía"),
        ("CC", "Cédula de ciudadanía (registro repetido)"),
        ("TI", "Tarjeta de identidad"),
        ("CE", "Cédula de extranjería"),
        ("RC", "Registro civil"),
        ("PE", "Permiso especial de permanencia"),
    ),
)

# BANCA, CORRESPONSAL y RETIRADO no aparecen en los datos: son canales del catálogo sin uso.
CANALES_VALIDOS = Fija(
    ("CANAL",),
    (("WEB",), ("TIENDA",), ("BANCA",), ("CORRESPONSAL",), ("RETIRADO",)),
)

ZONAS = Fija(
    ("ciudad", "zona"),
    (
        ("Villa Norte", "NORTE"),
        ("Puerto Sur", "SUR"),
        ("Valle Alto", "CENTRO"),
        ("Monte Verde", "ORIENTE"),
        ("Lago Azul", "OCCIDENTE"),
    ),
)

# Nueve pares (cliente, canal) distintos: la unión por dos columnas no repite filas.
METAS = Fija(
    ("id_cliente", "canal", "meta"),
    (
        ("101", "WEB", "500"),
        ("101", "TIENDA", "300"),
        ("102", "WEB", "200"),
        ("102", "TELEFONO", "400"),
        ("103", "TIENDA", "250"),
        ("104", "WEB", "900"),
        ("104", "TELEFONO", "150"),
        ("105", "TIENDA", "600"),
        ("106", "WEB", "350"),
    ),
)
