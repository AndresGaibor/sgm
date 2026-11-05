"""Entradas de los casos L2 (JOIN, IN, CASE, COALESCE, IS MISSING y validación con lookup).

Cada caso indica sus tablas. Los nombres de tabla son los nombres de archivo CSV sin extensión.
"""

from __future__ import annotations

from .datos_ficticios import Entrada
from .esquemas_corpus import clientes, ventas
from .esquemas_l2l3 import (
    CANALES_VALIDOS,
    HOMOLOGACION_DUP,
    HOMOLOGACION_TPO_DOC,
    METAS,
    TIPOS_CON_CC_FRECUENTE,
    ZONAS,
    Fija,
    operaciones,
)

ESPECIFICACIONES_L2: dict[str, dict[str, Entrada | Fija]] = {
    "l2_01_inner_join_clientes_ventas": {"clientes": clientes(8), "ventas": ventas(12)},
    # Faltantes: monto vacío en dos ventas, que pasan al resultado del LEFT JOIN.
    "l2_02_left_join_con_faltantes": {
        "clientes": clientes(10),
        "ventas": ventas(10, vacios_monto=2),
    },
    "l2_03_join_dos_columnas_en_on": {"ventas": ventas(14), "metas": METAS},
    # Validación con lookup: un tipo de documento vacío es inválido.
    "l2_04_validacion_tipo_doc": {
        "operaciones": operaciones(12, vacios_tipo=1),
        "homologacion_tpo_doc": HOMOLOGACION_TPO_DOC,
    },
    # Claves repetidas en la búsqueda: las operaciones con 'CC' se multiplican.
    "l2_05_lookup_claves_repetidas": {
        "operaciones": operaciones(12, tipos=TIPOS_CON_CC_FRECUENTE),
        "homologacion_tpo_doc_dup": HOMOLOGACION_DUP,
    },
    "l2_06_in_subconsulta": {"clientes": clientes(10), "ventas": ventas(14)},
    "l2_07_not_in_subconsulta": {"clientes": clientes(10), "ventas": ventas(14)},
    # Faltantes: monto vacío en dos ventas; esas filas caen en la rama ELSE.
    "l2_08_case_when_tras_left_join": {
        "clientes": clientes(8),
        "ventas": ventas(12, vacios_monto=2),
    },
    "l2_09_coalesce_tras_left_join": {
        "clientes": clientes(10),
        "ventas": ventas(11, vacios_monto=2),
    },
    # Faltantes numéricos (saldo) y de texto (ciudad).
    "l2_10_is_missing_numerico_y_texto": {
        "clientes": clientes(12, vacios_saldo=3, vacios_ciudad=2),
    },
    "l2_11_join_tres_tablas": {
        "clientes": clientes(10),
        "ventas": ventas(16),
        "zonas": ZONAS,
    },
    "l2_12_auto_join_misma_ciudad": {"clientes": clientes(12)},
    "l2_13_anti_join_sin_ventas": {"clientes": clientes(10), "ventas": ventas(8)},
    "l2_14_inner_join_where_orden": {
        "clientes": clientes(10),
        "ventas": ventas(16, vacios_monto=2),
    },
    "l2_15_validacion_en_cascada": {
        "operaciones": operaciones(14),
        "homologacion_tpo_doc": HOMOLOGACION_TPO_DOC,
        "canales_validos": CANALES_VALIDOS,
    },
}
