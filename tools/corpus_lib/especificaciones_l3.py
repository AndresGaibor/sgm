"""Entradas de los casos L3 (agregados, totales, conciliación y preparación con DATA step).

Cada caso indica sus tablas. Los faltantes que se cuentan en las invariantes están plantados aquí.
"""

from __future__ import annotations

from .datos_ficticios import Entrada
from .esquemas_corpus import clientes, productos, ventas
from .esquemas_l2l3 import HOMOLOGACION_DUP, Fija, columnas_depositos, facturas, operaciones

ESPECIFICACIONES_L3: dict[str, dict[str, Entrada | Fija]] = {
    # Faltantes plantados: saldo vacío en tres filas (las invariantes lo cuentan).
    "l3_01_count_star_vs_count_col": {"clientes": clientes(12, vacios_saldo=3)},
    "l3_02_sum_min_max_avg_faltantes": {"ventas": ventas(12, vacios_monto=3)},
    "l3_03_group_by_una_columna": {"clientes": clientes(12, vacios_ciudad=1)},
    "l3_04_group_by_varias_columnas": {"clientes": clientes(14, vacios_saldo=2)},
    "l3_05_having_conteo": {"clientes": clientes(14)},
    "l3_06_count_distinct": {"ventas": ventas(14), "clientes": clientes(10)},
    "l3_07_total_origen_y_salida": {"ventas": ventas(12, vacios_monto=1)},
    # Faltantes plantados: dos saldos de texto vacíos antes del DATA step.
    "l3_08_preparacion_input_left": {"columnas_depositos": columnas_depositos(12, vacios=2)},
    "l3_09_conciliacion_diferencia_plantada": {
        "operaciones": operaciones(14),
        "homologacion_tpo_doc_dup": HOMOLOGACION_DUP,
    },
    "l3_10_suma_decimales": {"facturas": facturas(20)},
    "l3_11_agregado_con_join": {"clientes": clientes(10), "ventas": ventas(12)},
    "l3_12_having_suma": {"productos": productos(14, vacios_stock=2)},
}
