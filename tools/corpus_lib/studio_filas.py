"""Comparación de tablas CSV del corpus, celda a celda y fila a fila.

Reglas (plan de corpus, sección 6):
- Las columnas tienen el mismo nombre y el mismo orden. `ignorar_orden_columnas` acepta otro orden.
- Las filas se comparan como conjunto, salvo que el caso declare `orden_relevante: true`.
- Los números se comparan con la `tolerancia` del caso. El texto ignora los blancos finales.
  Una celda vacía es igual a otra vacía.

En modo conjunto, las filas que coinciden exactamente se emparejan primero. Las que sobran de
uno y otro lado se emparejan por orden de clave y se comparan celda a celda. Lo que no tiene
pareja se reporta como faltante o sobrante. El número de fila de una celda es el de `esperado/`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_NUMERO = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?$")
Fila = list[str]


@dataclass(frozen=True)
class Diferencia:
    """Una diferencia concreta. `tipo` es columnas, filas, celda, faltante, sobrante o archivo."""

    tipo: str
    mensaje: str = ""
    fila: int | None = None
    columna: str | None = None
    esperado: str | None = None
    obtenido: str | None = None

    def texto(self) -> str:
        """Descripción legible de la diferencia, en una línea."""
        if self.tipo == "celda":
            return (
                f"fila {self.fila}, columna '{self.columna}': "
                f"esperado '{self.esperado}', obtenido '{self.obtenido}'"
            )
        if self.tipo == "faltante":
            return f"fila {self.fila} de esperado no aparece en la salida: {self.esperado}"
        if self.tipo == "sobrante":
            return f"fila {self.fila} de la salida no esperada: {self.obtenido}"
        return self.mensaje


def _texto(celda: str | None) -> str:
    """Celda normalizada: vacío es cadena vacía y los blancos finales se ignoran."""
    return "" if celda is None else celda.rstrip()


def _numero(texto: str) -> float | None:
    return float(texto) if _NUMERO.match(texto) else None


def iguales(esperado: str, obtenido: str, tolerancia: float) -> bool:
    """Dos celdas normalizadas son iguales si son el mismo texto o dos números a `tolerancia`."""
    if esperado == obtenido:
        return True
    numero_esperado, numero_obtenido = _numero(esperado), _numero(obtenido)
    if numero_esperado is None or numero_obtenido is None:
        return False
    return abs(numero_esperado - numero_obtenido) <= tolerancia


def _clave_celda(texto: str) -> tuple:
    """Orden determinista: vacío primero, luego números y después texto."""
    if texto == "":
        return (0, 0.0, "")
    numero = _numero(texto)
    if numero is not None:
        return (1, numero, "")
    return (2, 0.0, texto)


def _clave_fila(fila: Fila) -> tuple:
    return tuple(_clave_celda(celda) for celda in fila)


def _filas_iguales(esperada: Fila, obtenida: Fila, tolerancia: float) -> bool:
    return len(esperada) == len(obtenida) and all(
        iguales(e, o, tolerancia) for e, o in zip(esperada, obtenida, strict=True)
    )


def _diferencias_fila(
    numero: int, esperada: Fila, obtenida: Fila, columnas: list[str], tolerancia: float
) -> list[Diferencia]:
    return [
        Diferencia("celda", fila=numero, columna=columna, esperado=e, obtenido=o)
        for columna, e, o in zip(columnas, esperada, obtenida, strict=True)
        if not iguales(e, o, tolerancia)
    ]


def _columnas(
    esperadas: list[str], obtenidas: list[str], ignorar_orden: bool
) -> tuple[list[Diferencia], list[int] | None]:
    """Diferencias de columnas y, si son comparables, el índice de cada columna obtenida."""
    if esperadas == obtenidas:
        return [], list(range(len(esperadas)))
    if ignorar_orden and sorted(esperadas) == sorted(obtenidas):
        return [], [obtenidas.index(nombre) for nombre in esperadas]
    faltan = [c for c in esperadas if c not in obtenidas]
    sobran = [c for c in obtenidas if c not in esperadas]
    if faltan or sobran:
        mensaje = f"columnas: faltan {faltan}, sobran {sobran}"
    else:
        mensaje = (
            f"columnas: mismo nombre en distinto orden: "
            f"esperado {esperadas}, obtenido {obtenidas}"
        )
    return [Diferencia("columnas", mensaje)], None


def _unir(fila: Fila) -> str:
    return "(" + ", ".join(fila) + ")"


def _por_posicion(
    esperadas: list[Fila], obtenidas: list[Fila], columnas: list[str], tolerancia: float
) -> list[Diferencia]:
    diferencias: list[Diferencia] = []
    comunes = min(len(esperadas), len(obtenidas))
    for indice in range(comunes):
        diferencias += _diferencias_fila(
            indice + 1, esperadas[indice], obtenidas[indice], columnas, tolerancia
        )
    diferencias += [
        Diferencia("faltante", fila=i + 1, esperado=_unir(esperadas[i]))
        for i in range(comunes, len(esperadas))
    ]
    diferencias += [
        Diferencia("sobrante", fila=i + 1, obtenido=_unir(obtenidas[i]))
        for i in range(comunes, len(obtenidas))
    ]
    return diferencias


def _como_conjunto(
    esperadas: list[Fila], obtenidas: list[Fila], columnas: list[str], tolerancia: float
) -> list[Diferencia]:
    """Compara sin orden: primero las filas idénticas, luego las sobrantes por clave."""
    disponibles: dict[tuple, list[int]] = {}
    for indice, fila in enumerate(obtenidas):
        disponibles.setdefault(tuple(fila), []).append(indice)
    usadas: set[int] = set()
    sin_pareja: list[int] = []
    for indice, fila in enumerate(esperadas):
        libres = disponibles.get(tuple(fila))
        if libres:
            usadas.add(libres.pop(0))
        else:
            sin_pareja.append(indice)
    libres = [j for j in range(len(obtenidas)) if j not in usadas]
    # Pasada tolerante: solo para las filas que no casaron exactamente.
    restantes: list[int] = []
    for indice in sin_pareja:
        for posicion, j in enumerate(libres):
            if _filas_iguales(esperadas[indice], obtenidas[j], tolerancia):
                del libres[posicion]
                break
        else:
            restantes.append(indice)
    restantes.sort(key=lambda i: _clave_fila(esperadas[i]))
    libres.sort(key=lambda j: _clave_fila(obtenidas[j]))
    diferencias: list[Diferencia] = []
    for indice, j in zip(restantes, libres, strict=False):
        diferencias += _diferencias_fila(
            indice + 1, esperadas[indice], obtenidas[j], columnas, tolerancia
        )
    diferencias += [
        Diferencia("faltante", fila=i + 1, esperado=_unir(esperadas[i]))
        for i in restantes[len(libres):]
    ]
    diferencias += [
        Diferencia("sobrante", fila=j + 1, obtenido=_unir(obtenidas[j]))
        for j in libres[len(restantes):]
    ]
    return diferencias


def comparar_tablas(
    esperada: tuple[list[str], list[list[str | None]]],
    obtenida: tuple[list[str], list[list[str | None]]],
    *,
    tolerancia: float = 0.0,
    orden_relevante: bool = False,
    ignorar_orden_columnas: bool = False,
) -> list[Diferencia]:
    """Compara dos tablas `(columnas, filas)` tal como las devuelve `csv_tabla.leer_csv`.

    Si las columnas no son comparables, se devuelve solo esa diferencia: sin columnas
    comparables no tiene sentido comparar filas.
    """
    columnas_esperadas, filas_esperadas = esperada
    columnas_obtenidas, filas_obtenidas = obtenida
    diferencias, orden = _columnas(columnas_esperadas, columnas_obtenidas, ignorar_orden_columnas)
    if orden is None:
        return diferencias
    esperadas = [[_texto(celda) for celda in fila] for fila in filas_esperadas]
    obtenidas = [[_texto(fila[posicion]) for posicion in orden] for fila in filas_obtenidas]
    if len(esperadas) != len(obtenidas):
        diferencias.append(
            Diferencia("filas", f"filas: esperado {len(esperadas)}, obtenido {len(obtenidas)}")
        )
    if orden_relevante:
        diferencias += _por_posicion(esperadas, obtenidas, columnas_esperadas, tolerancia)
    else:
        diferencias += _como_conjunto(esperadas, obtenidas, columnas_esperadas, tolerancia)
    return diferencias
