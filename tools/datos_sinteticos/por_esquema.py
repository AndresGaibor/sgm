"""Datos sintéticos deterministas para columnas con tipos declarados."""

from collections.abc import Mapping, Sequence

from sgm.ir.models import Column
from tools.corpus_lib.datos_ficticios import Entrada, col, generar_tabla
from tools.datos_sinteticos.validacion import validar_columnas, validar_valor


def entrada_desde_esquema(columnas: Sequence[Column], filas: int) -> Entrada:
    """Convierte los tipos demostrados en generadores; los demás producen códigos de texto."""
    if filas < 0:
        raise ValueError("filas no puede ser negativo")
    validar_columnas([c.name for c in columnas])
    resultado = []
    for columna in columnas:
        if columna.type == "Double":
            resultado.append(col(columna.name, "decimal", 1, 1000))
        elif columna.type in {"Integer", "Long"}:
            resultado.append(col(columna.name, "entero", 1, 1000))
        else:
            resultado.append(col(columna.name, "codigo", f"SIM_{columna.name}", 1))
    return Entrada(filas, tuple(resultado))


def generar_filas(
    tabla: str,
    columnas: Sequence[Column],
    filas: int,
    semilla: int = 20261104,
    exigidos: Mapping[str, Sequence[str]] | None = None,
    *,
    fijos_por_fila: Sequence[Mapping[str, str]] = (),
) -> tuple[list[str], list[list[str]], list[str]]:
    """Genera filas y avisa de tipos no soportados, sin suponer valores externos."""
    nombres, datos = generar_tabla(f"{semilla}:{tabla}", entrada_desde_esquema(columnas, filas))
    indices = {nombre.casefold(): i for i, nombre in enumerate(nombres)}
    for nombre, valores in (exigidos or {}).items():
        if nombre.casefold() not in indices:
            raise ValueError(f"{tabla}: columna exigida desconocida {nombre}")
        if len(valores) > filas:
            raise ValueError(f"{tabla}.{nombre}: faltan filas para valores exigidos")
        for i, valor in enumerate(valores):
            indice = indices[nombre.casefold()]
            datos[i][indice] = validar_valor(valor, columnas[indice].type)
    por_columna = {columna.name.casefold(): columna for columna in columnas}
    if len(fijos_por_fila) > filas:
        raise ValueError(f"{tabla}: fijos_por_fila tiene más filas que el manifiesto")
    for numero, valores in enumerate(fijos_por_fila):
        for nombre, valor in valores.items():
            indice = indices.get(nombre.casefold())
            if indice is None:
                raise ValueError(f"{tabla}: columna fija por fila no declarada: {nombre}")
            try:
                datos[numero][indice] = validar_valor(valor, por_columna[nombre.casefold()].type)
            except ValueError as error:
                raise ValueError(f"{tabla}.{nombre}, fila {numero + 1}: {error}") from error
    avisos = [
        f"P-TIPO-GENERADOR {tabla}.{c.name}: tipo {c.type} sin generador; se usa texto"
        for c in columnas
        if c.type not in {None, "String", "Double", "Integer", "Long"}
    ]
    return nombres, datos, avisos
