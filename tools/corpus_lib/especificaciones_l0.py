"""Entradas de los casos L0 (DATA step). Cada caso lista sus CSV con filas y columnas."""

from __future__ import annotations

from .datos_ficticios import Entrada
from .esquemas_corpus import clientes, productos, ventas

ESPECIFICACIONES_L0: dict[str, dict[str, Entrada]] = {
    "l0_01_where_sentencia": {"clientes": clientes(6, saldo=(0, 3000))},
    "l0_02_where_opcion": {"clientes": clientes(7, saldo=(0, 3000))},
    "l0_03_keep": {"clientes": clientes(8)},
    "l0_04_drop": {"productos": productos(6)},
    "l0_05_rename": {"clientes": clientes(5)},
    "l0_06_asignacion": {"productos": productos(7)},
    "l0_07_if_then_else": {"clientes": clientes(9, saldo=(0, 3000))},
    "l0_08_concatenar": {"clientes": clientes(6)},
    "l0_09_set_dos_tablas": {
        "ventas_enero": ventas(4, id_inicio=1),
        "ventas_febrero": ventas(3, id_inicio=101),
    },
    "l0_10_if_subsetting": {"ventas": ventas(8)},
    "l0_11_rename_keep": {"productos": productos(5)},
    "l0_12_bandera_numerica": {"productos": productos(6)},
    "l0_13_do_end": {"clientes": clientes(7, saldo=(-300, 2000))},
    "l0_14_where_drop": {"ventas": ventas(9)},
    "l0_15_importar_exportar": {"productos": productos(6)},
}
