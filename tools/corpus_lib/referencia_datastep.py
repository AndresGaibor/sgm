"""Referencia en Python de la semántica de DATA step y PROC SORT que usan los casos L6.

No hay SAS en el entorno: estas funciones son el oráculo de capa B para `MERGE ... BY`, `IN=`,
`FIRST.`/`LAST.`, acumulados con `RETAIN` o la sentencia suma, y `PROC SORT` con `NODUPKEY` o
`NODUP`. Cada función indica la regla de SAS que implementa y su fuente.

Una tabla es una lista de diccionarios (columna -> valor, `None` para faltante). Las entradas de
`merge_by` deben venir ordenadas por la llave BY, como exige SAS; si no lo están, la función falla
en vez de reordenar en silencio.

Fuentes (consultadas el 4 de noviembre de 2026):
- MERGE: https://go.documentation.sas.com/api/docsets/lestmtsref/9.4/content/n1i8w2bwu1fn5kn1gpxj18xttbb0.htm
  "The MERGE statement does not produce a Cartesian product on a many-to-many match-merge."
  "it performs a one-to-one merge while there are observations in the BY group in at least one data
  set." "When all observations in the BY group have been read from one data set and there are still
  more observations in another data set, SAS performs a one-to-many merge until all BY group
  observations have been read." "The number of observations in the new data set is the sum of the
  largest number of observations in each BY group in all data sets."
- Ejemplo de muchos a muchos (tablas ONE y TWO, salida de PROC PRINT): https://support.sas.com/kb/24/752.html
  "A DATA step that performs a many-to-many merge does not produce a Cartesian product across a
  BY-group." Nota del log: "MERGE statement has more than one data set with repeats of BY values."
- FIRST. y LAST.: https://support.sas.com/documentation/cdl/en/lrcon/65287/HTML/default/p0e9b2d12lpyjkn1b0y1tqg6q146.htm
- NODUPKEY y NODUP: sin fuente oficial consultada; ver `pendiente_revision` en los casos.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

Fila = dict
URL_MERGE = (
    "https://go.documentation.sas.com/api/docsets/lestmtsref/9.4/content/"
    "n1i8w2bwu1fn5kn1gpxj18xttbb0.htm"
)
URL_MUCHOS_A_MUCHOS = "https://support.sas.com/kb/24/752.html"
URL_BY_GROUPS = (
    "https://support.sas.com/documentation/cdl/en/lrcon/65287/HTML/default/"
    "p0e9b2d12lpyjkn1b0y1tqg6q146.htm"
)


def _orden(valor: object) -> tuple:
    """Clave de orden de SAS: el faltante va primero, luego el resto en su orden natural."""
    return (0,) if valor is None else (1, valor)


def _clave_orden(fila: Fila, by: list[str]) -> tuple:
    return tuple(_orden(fila.get(columna)) for columna in by)


def _llave(fila: Fila, by: list[str]) -> tuple:
    return tuple(fila.get(columna) for columna in by)


def _grupos(filas: list[Fila], by: list[str]) -> list[tuple[tuple, list[Fila]]]:
    """Agrupa filas contiguas con la misma llave. Exige que la entrada esté ordenada por BY."""
    grupos: list[tuple[tuple, list[Fila]]] = []
    vistas: set[tuple] = set()
    for fila in filas:
        llave = _llave(fila, by)
        if grupos and grupos[-1][0] == llave:
            grupos[-1][1].append(fila)
            continue
        if grupos and _clave_orden(fila, by) < _clave_orden(grupos[-1][1][0], by):
            raise ValueError(f"la entrada no está ordenada por BY {by}: aparece {llave} tarde")
        if llave in vistas:
            raise ValueError(f"la entrada no está ordenada por BY {by}: {llave} no es contiguo")
        vistas.add(llave)
        grupos.append((llave, [fila]))
    return grupos


def merge_by(
    conjuntos: list[list[Fila]],
    by: list[str],
    indicadores: list[str] | None = None,
) -> list[Fila]:
    """DATA step `MERGE conjunto1 ... conjuntoN; BY by;` con `IN=` opcionales.

    Por cada valor de BY, el número de filas de salida es el máximo de filas que tiene cada
    conjunto en ese grupo (regla de la documentación de MERGE). En la fila k, cada conjunto aporta
    su observación k; si ya se acabó, conserva la última (los valores se retienen en el PDV). No
    hay producto cartesiano. `indicadores[i]` vale 1 si el conjunto i tiene el grupo, 0 si no.
    Las columnas que no son BY vienen de cada conjunto; si dos conjuntos tienen la misma columna
    no BY, gana el último, como en SAS. Un conjunto sin observaciones en el grupo deja sus columnas
    en `None`: ese caso no está verificado contra SAS y no lo usan los casos.
    """
    if indicadores is not None and len(indicadores) != len(conjuntos):
        raise ValueError("indicadores debe tener un nombre por conjunto")
    mapas = [_grupos(filas, by) for filas in conjuntos]
    llaves = sorted(
        {llave for mapa in mapas for llave, _ in mapa},
        key=lambda llave: tuple(_orden(valor) for valor in llave),
    )
    salida: list[Fila] = []
    for llave in llaves:
        por_conjunto = [_buscar(mapa, llave) for mapa in mapas]
        repeticiones = max(len(grupo) for grupo in por_conjunto)
        for k in range(repeticiones):
            fila: Fila = dict(zip(by, llave, strict=True))
            for indice, grupo in enumerate(por_conjunto):
                if grupo:
                    fila.update(_sin_by(grupo[min(k, len(grupo) - 1)], by))
                else:
                    columnas = _columnas_no_by(conjuntos[indice], by)
                    fila.update({columna: None for columna in columnas})
                if indicadores is not None:
                    fila[indicadores[indice]] = 1 if grupo else 0
            salida.append(fila)
    return salida


def _buscar(mapa: list[tuple[tuple, list[Fila]]], llave: tuple) -> list[Fila]:
    for clave, grupo in mapa:
        if clave == llave:
            return grupo
    return []


def _sin_by(fila: Fila, by: list[str]) -> Fila:
    return {columna: valor for columna, valor in fila.items() if columna not in by}


def _columnas_no_by(filas: list[Fila], by: list[str]) -> list[str]:
    nombres: list[str] = []
    for fila in filas:
        for columna in fila:
            if columna not in by and columna not in nombres:
                nombres.append(columna)
    return nombres


def marcas_first_last(filas: list[Fila], by: list[str]) -> list[Fila]:
    """Copia de cada fila con `FIRST.v` y `LAST.v` para cada variable BY `v`.

    Como en SAS, `FIRST.v` vale 1 si la fila abre un grupo con el mismo valor de `v` y de las
    variables anteriores del BY (es decir, el prefijo de la llave cambia). `LAST.v` es lo mismo
    mirando a la fila siguiente. Las variables FIRST./LAST. no pasan a la salida del paso DATA;
    aquí se devuelven como columnas para poder comprobarlas.
    """
    _grupos(filas, by)
    salida: list[Fila] = []
    for indice, fila in enumerate(filas):
        copia = dict(fila)
        for corte, columna in enumerate(by, start=1):
            prefijo = by[:corte]
            actual = _llave(fila, prefijo)
            anterior = _llave(filas[indice - 1], prefijo) if indice > 0 else None
            siguiente = _llave(filas[indice + 1], prefijo) if indice + 1 < len(filas) else None
            copia[f"FIRST.{columna}"] = int(indice == 0 or anterior != actual)
            copia[f"LAST.{columna}"] = int(siguiente is None or siguiente != actual)
        salida.append(copia)
    return salida


def acumulado_por_grupo(filas: list[Fila], by: list[str], columna: str, nombre: str) -> list[Fila]:
    """Sentencia suma `nombre + columna` con reinicio en cada grupo (`IF FIRST.g THEN nombre=0`).

    Un valor faltante no suma (la sentencia suma ignora los faltantes). El reinicio usa el último
    nivel de BY. Los casos L6 que usan esto indican la fuente de la regla en su `caso.yaml`.
    """
    salida: list[Fila] = []
    total = 0
    for fila in marcas_first_last(filas, by):
        if fila[f"FIRST.{by[-1]}"]:
            total = 0
        valor = fila[columna]
        if valor is not None:
            total += valor
        copia = {k: v for k, v in fila.items() if not k.startswith(("FIRST.", "LAST."))}
        copia[nombre] = total
        salida.append(copia)
    return salida


def contador_retain(filas: list[Fila], by: list[str], nombre: str) -> list[Fila]:
    """`RETAIN nombre 0; nombre + 1;` con reinicio por grupo. Equivale a un acumulado de unos."""
    marcadas = [dict(fila, UNO=1) for fila in filas]
    return acumulado_por_grupo(marcadas, by, "UNO", nombre)


def ultima_de_grupo(filas: list[Fila], by: list[str]) -> list[Fila]:
    """`IF LAST.g;`: conserva la última fila de cada grupo BY, sin las marcas."""
    return [
        {k: v for k, v in fila.items() if not k.startswith(("FIRST.", "LAST."))}
        for fila in marcas_first_last(filas, by)
        if fila[f"LAST.{by[-1]}"]
    ]


def proc_sort(filas: list[Fila], by: list[str], nodupkey: bool = False) -> list[Fila]:
    """`PROC SORT BY by; [NODUPKEY]`. La ordenación es estable: dentro de una llave se mantiene el
    orden de entrada.

    Con `NODUPKEY` se conserva la primera fila de cada llave en el orden de salida. Esa regla de
    conservación viene de fuentes secundarias (ver `pendiente_revision` en los casos L6).
    """
    ordenadas = sorted(filas, key=lambda fila: _clave_orden(fila, by))
    if not nodupkey:
        return ordenadas
    salida: list[Fila] = []
    vistas: set[tuple] = set()
    for fila in ordenadas:
        llave = _llave(fila, by)
        if llave not in vistas:
            vistas.add(llave)
            salida.append(fila)
    return salida


def proc_sort_nodup(filas: list[Fila], columnas: Iterable[str]) -> list[Fila]:
    """`PROC SORT BY _ALL_; NODUP` simulado: ordena por todas las columnas y quita las filas
    idénticas a la anterior. Con la ordenación completa, eso equivale a quitar duplicados exactos.
    """
    orden = list(columnas)
    ordenadas = sorted(filas, key=lambda fila: _clave_orden(fila, orden))
    salida: list[Fila] = []
    for fila in ordenadas:
        if not salida or any(fila.get(c) != salida[-1].get(c) for c in orden):
            salida.append(fila)
    return salida


def aplicar_en_orden(
    filas: list[Fila], pasos: list[Callable[[list[Fila]], list[Fila]]]
) -> list[Fila]:
    """Encadena pasos de tabla (cada uno toma y devuelve filas)."""
    for paso in pasos:
        filas = paso(filas)
    return filas
