"""Esquemas de las tablas ficticias de los casos: clientes, productos y ventas.

Cada función devuelve una `Entrada` con el número de filas y las opciones que cambian el caso
(nombres con tildes, celdas vacías, rango de valores). Las especificaciones de cada caso las usan.
"""

from __future__ import annotations

from .datos_ficticios import (
    CANALES,
    CATEGORIAS,
    CIUDADES,
    DESCRIPCIONES,
    ESTADOS,
    NOMBRES,
    Entrada,
    col,
)


def clientes(
    n: int,
    *,
    saldo: tuple[int, int] = (0, 5000),
    nombres: tuple[str, ...] = NOMBRES,
    vacios_saldo: int = 0,
    vacios_ciudad: int = 0,
) -> Entrada:
    """Clientes: id, nombre, ciudad, saldo (entero) y estado."""
    return Entrada(
        n,
        (
            col("id_cliente", "secuencia", 101),
            col("nombre", "elige", nombres),
            col("ciudad", "elige", CIUDADES, vacios=vacios_ciudad),
            col("saldo", "entero", *saldo, vacios=vacios_saldo),
            col("estado", "elige", ESTADOS),
        ),
    )


def productos(
    n: int,
    *,
    base: int = 1,
    descripciones: tuple[str, ...] = DESCRIPCIONES,
    vacios_stock: int = 0,
) -> Entrada:
    """Productos: código PRD-nnn, descripción, precio, stock y categoría."""
    return Entrada(
        n,
        (
            col("codigo", "codigo", "PRD", base),
            col("descripcion", "elige", descripciones),
            col("precio", "entero", 5, 300),
            col("stock", "entero", 0, 80, vacios=vacios_stock),
            col("categoria", "elige", CATEGORIAS),
        ),
    )


def ventas(
    n: int,
    *,
    id_inicio: int = 1,
    meses: tuple[int, int] = (1, 4),
    vacios_monto: int = 0,
    vacios_cantidad: int = 0,
) -> Entrada:
    """Ventas: id, cliente, fecha (2026), monto, canal y cantidad."""
    return Entrada(
        n,
        (
            col("id_venta", "secuencia", id_inicio),
            col("id_cliente", "entero", 101, 110),
            col("fecha", "fecha", 2026, *meses),
            col("monto", "entero", 50, 900, vacios=vacios_monto),
            col("canal", "elige", CANALES),
            col("cantidad", "entero", 1, 9, vacios=vacios_cantidad),
        ),
    )
