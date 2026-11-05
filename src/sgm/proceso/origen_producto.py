"""Origen de datos de cada producto: el archivo delimitado principal y su esquema deducido.

De los archivos que el SAS baja e importa, el principal de un producto es el más ancho de los que
se le asignan; los demás son auxiliares (listas de clientes, por ejemplo) y quedan como pendientes.
Las columnas por posición toman el primer nombre que el SAS demuestre en cualquiera de los
productos: los productos con la misma anchura comparten estructura (decisión D6 del diseño).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.proceso.esquema_csv import ColumnaCsv, esquema_csv
from sgm.proceso.fuentes_csv import FuenteCsv, fuentes_csv


@dataclass(frozen=True)
class OrigenProducto:
    producto: str
    fuente: FuenteCsv
    columnas: tuple[ColumnaCsv, ...]


@dataclass
class OrigenesProducto:
    por_producto: dict[str, OrigenProducto] = field(default_factory=dict)
    columnas_comunes: tuple[str, ...] = ()  # nombre por posición, común a los productos
    # Columna -> (w, d) del informat que el SAS demuestra. Solo las que algún producto convierte.
    numericas_comunes: dict[str, tuple[int, int]] = field(default_factory=dict)
    pendientes: list[str] = field(default_factory=list)


def origenes_producto(texto: str, productos: dict[str, tuple[str, ...]]) -> OrigenesProducto:
    """Archivo principal por producto y nombres de columna comunes. Lo dudoso queda pendiente."""
    resultado = OrigenesProducto()
    fuentes = fuentes_csv(texto, productos)
    for fuente in fuentes:
        if fuente.producto is None:
            resultado.pendientes.append(f"{fuente.archivo}: no se asigna a ningún producto")
    for producto in productos:
        propias = [f for f in fuentes if f.producto == producto]
        if not propias:
            resultado.pendientes.append(f"{producto}: el SAS no importa ningún archivo suyo")
            continue
        principal = max(propias, key=lambda f: f.columnas)  # empate: el primero
        for otra in propias:
            if otra is not principal:
                resultado.pendientes.append(
                    f"{producto}: {otra.archivo} ({otra.columnas} columnas) es auxiliar de "
                    f"{principal.archivo} ({principal.columnas} columnas)"
                )
        resultado.por_producto[producto] = OrigenProducto(
            producto, principal, tuple(esquema_csv(texto, principal))
        )
    anchos = {len(o.columnas) for o in resultado.por_producto.values()}
    if len(anchos) > 1:
        resultado.pendientes.append(f"los productos tienen anchuras distintas de archivo: {anchos}")
    ancho = max(anchos, default=0)
    nombres = []
    for n in range(ancho):
        columnas = [
            o.columnas[n] for o in resultado.por_producto.values() if n < len(o.columnas)
        ]
        demostrados = [c.nombre for c in columnas if c.demostrada]
        nombre = demostrados[0] if demostrados else f"VAR{n + 1}"
        nombres.append(nombre)
        informats = {(c.ancho, c.decimales) for c in columnas if c.numerica}
        if informats:
            resultado.numericas_comunes[nombre] = sorted(informats)[0]
            if len(informats) > 1:
                resultado.pendientes.append(
                    f"{nombre}: los productos declaran informats distintos {sorted(informats)}"
                )
    resultado.columnas_comunes = tuple(nombres)
    return resultado
