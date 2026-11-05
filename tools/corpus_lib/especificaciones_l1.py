"""Entradas de los casos L1 (PROC SQL).

Cuatro casos tienen celdas vacías y tres tienen tildes o Ñ en los datos.
"""

from __future__ import annotations

from .datos_ficticios import (
    DESCRIPCIONES_CON_TILDES,
    NOMBRES_CON_TILDES,
    Entrada,
)
from .esquemas_corpus import clientes, productos, ventas

ESPECIFICACIONES_L1: dict[str, dict[str, Entrada]] = {
    "l1_01_select_columnas": {"clientes": clientes(7)},
    "l1_02_where_y_or": {"clientes": clientes(9)},
    # Faltantes: saldo vacío en dos filas.
    "l1_03_orden_con_faltantes": {"clientes": clientes(8, vacios_saldo=2)},
    "l1_04_distinct_orden": {"clientes": clientes(10)},
    # Faltantes: monto y cantidad vacíos.
    "l1_05_aritmetica_faltantes": {"ventas": ventas(8, vacios_monto=1, vacios_cantidad=2)},
    # Tildes y Ñ en los nombres.
    "l1_06_like_con_tildes": {"clientes": clientes(8, nombres=NOMBRES_CON_TILDES)},
    "l1_07_like_guion_bajo": {"productos": productos(10, base=95)},
    "l1_08_in_lista": {"clientes": clientes(9)},
    "l1_09_between_fechas": {"ventas": ventas(10, meses=(1, 4))},
    # Faltantes: stock vacío en dos filas, que pasan a la segunda etapa.
    "l1_10_dos_etapas_faltantes": {"productos": productos(8, vacios_stock=2)},
    "l1_11_orden_posicional": {"ventas": ventas(7)},
    # Tildes y Ñ en las descripciones.
    "l1_12_filtro_tildes": {
        "productos": productos(8, descripciones=DESCRIPCIONES_CON_TILDES)
    },
    # Faltantes: ciudad vacía en dos filas y saldo vacío en una.
    "l1_13_seleccion_faltantes": {"clientes": clientes(8, vacios_ciudad=2, vacios_saldo=1)},
    "l1_14_expresion_compuesta": {"ventas": ventas(12)},
    # Tildes y Ñ en los nombres, con DISTINCT.
    "l1_15_distinct_tildes": {"clientes": clientes(9, nombres=NOMBRES_CON_TILDES)},
}
