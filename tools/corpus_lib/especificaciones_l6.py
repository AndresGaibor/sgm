"""Especificaciones de los casos L6: MERGE con BY, IN=, FIRST./LAST., RETAIN y PROC SORT.

El esperado sale de `referencia_datastep.py` (capa B). Cada caso declara sus entradas y una
función `calculo` que devuelve las filas de salida en el orden del DATA step. Las reglas sin
fuente oficial consultada marcan el caso `pendiente_revision`.
"""

from .referencia_datastep import (
    URL_BY_GROUPS,
    URL_MERGE,
    URL_MUCHOS_A_MUCHOS,
    URL_OUTPUT,
    acumulado_por_grupo,
    contador_retain,
    merge_by,
    proc_sort,
    proc_sort_nodup,
    ultima_de_grupo,
)

Entradas = dict[str, dict]


def _proyectar(filas: list[dict], columnas: list[str]) -> list[dict]:
    return [{c: fila[c] for c in columnas} for fila in filas]


def _calc_uno_a_uno(e: Entradas) -> list[dict]:
    return merge_by([e["CLIENTES"], e["SALDOS"]], ["ID"])


def _calc_muchos(e: Entradas) -> list[dict]:
    return merge_by([e["ONE"], e["TWO"]], ["id"])


def _calc_in(e: Entradas) -> list[dict]:
    filas = merge_by([e["CLIENTES"], e["PAGOS"]], ["ID"], ["EN_CLIENTES", "EN_PAGOS"])
    return _proyectar(filas, ["ID", "EN_CLIENTES", "EN_PAGOS"])


def _calc_tres(e: Entradas) -> list[dict]:
    return merge_by([e["CAFE"], e["SNACK"], e["VENDING"]], ["id"])


def _calc_ultima(e: Entradas) -> list[dict]:
    return ultima_de_grupo(e["VENTAS"], ["CIUDAD"])


def _calc_acumulado(e: Entradas) -> list[dict]:
    return acumulado_por_grupo(e["PAGOS_DEPTO"], ["DEPTO"], "PAGO", "ACUM")


def _calc_retain(e: Entradas) -> list[dict]:
    return contador_retain(e["EMPLEADOS"], ["DEPTO"], "CONTADOR")


def _calc_nodupkey(e: Entradas) -> list[dict]:
    return proc_sort(e["CLIENTES_DUP"], ["ID"], nodupkey=True)


def _calc_nodup(e: Entradas) -> list[dict]:
    return proc_sort_nodup(e["VENTAS_DUP"], ["ID", "TEXTO", "MONTO"])


def _calc_ultimo_por_llave(e: Entradas) -> list[dict]:
    return ultima_de_grupo(e["MOVIMIENTOS"], ["ID"])


def _calc_merge_acumulado(e: Entradas) -> list[dict]:
    fusion = merge_by([e["ZONAS"], e["VENTAS"]], ["ZONA"])
    return acumulado_por_grupo(fusion, ["ZONA"], "MONTO", "ACUM")


def _calc_ordenar_merge(e: Entradas) -> list[dict]:
    izquierda = proc_sort(e["NOMBRES"], ["ID"])
    derecha = proc_sort(e["SALDOS"], ["ID"])
    return merge_by([izquierda, derecha], ["ID"])


def _calc_output_multiple(e: Entradas) -> dict[str, list[dict]]:
    """Cada observación va a una o dos salidas según el valor, según OUTPUT y ELSE de SAS."""
    filas = e["REGISTROS"]
    bajas = [fila for fila in filas if fila["VALOR"] <= 2]
    altas = [fila for fila in filas if fila["VALOR"] > 2]
    return {"SALIDA_BAJA": bajas, "COPIA_BAJA": bajas, "SALIDA_ALTA": altas}


_URL_SORT = (
    "https://support.sas.com/documentation/cdl/en/hosto390/65144/HTML/default/"
    "p03pc2ubulklb5n1hhgpilswqaf6.htm"
)

ESPECIFICACIONES_L6: dict[str, dict] = {
    "l6_01_merge_by_uno_a_uno": {
        "construcciones": ["DATA STEP", "MERGE", "BY"],
        "entradas": {
            "CLIENTES": (["ID", "NOMBRE"], [(1, "Ana"), (2, "Bruno"), (3, "Carla")]),
            "SALDOS": (["ID", "SALDO"], [(1, 150), (2, 80), (3, 220)]),
        },
        "calculo": _calc_uno_a_uno,
        "columnas": ["ID", "NOMBRE", "SALDO"],
        "salida": "CLIENTES_CON_SALDO",
        "fuentes": [URL_MERGE, URL_BY_GROUPS],
        "invariantes": ["filas(CLIENTES_CON_SALDO) == 3", "suma(CLIENTES_CON_SALDO.SALDO) == 450"],
        "razonamiento": "Llaves únicas en ambos lados: un registro por llave, sin cruce.",
    },
    "l6_02_merge_muchos_a_muchos": {
        "construcciones": ["DATA STEP", "MERGE", "BY", "REPETIDOS EN AMBOS LADOS"],
        "entradas": {
            "ONE": (
                ["id", "fruit"],
                [
                    ("a", "apple"),
                    ("a", "apricot"),
                    ("b", "banana"),
                    ("c", "coconut"),
                    ("c", "cherry"),
                    ("c", "crabapple"),
                ],
            ),
            "TWO": (
                ["id", "color"],
                [("a", "amber"), ("b", "brown"), ("b", "black"), ("c", "cocoa"), ("c", "cream")],
            ),
        },
        "calculo": _calc_muchos,
        "columnas": ["id", "fruit", "color"],
        "salida": "BOTH",
        "fuentes": [URL_MUCHOS_A_MUCHOS, URL_MERGE],
        "invariantes": ["filas(BOTH) == 7"],
        "razonamiento": (
            "Ejemplo de la documentación (KB 24752). Salen 7 filas (2+2+3 por grupo), no el "
            "producto cartesiano (3x2 en c daría 6 filas)."
        ),
    },
    "l6_03_merge_in_flags": {
        "construcciones": ["DATA STEP", "MERGE", "BY", "IN="],
        "entradas": {
            "CLIENTES": (["ID", "NOMBRE"], [(1, "Ana"), (2, "Bruno"), (3, "Carla"), (4, "Diego")]),
            "PAGOS": (["ID", "MONTO"], [(2, 40), (4, 90), (5, 15)]),
        },
        "calculo": _calc_in,
        "columnas": ["ID", "EN_CLIENTES", "EN_PAGOS"],
        "salida": "COBERTURA_PAGOS",
        "fuentes": [URL_MERGE],
        "invariantes": ["filas(COBERTURA_PAGOS) == 5", "suma(COBERTURA_PAGOS.EN_PAGOS) == 3"],
        "razonamiento": (
            "IN= marca el origen de cada llave. Solo se conservan ID y las marcas: las columnas "
            "de un conjunto sin el grupo no están verificadas."
        ),
    },
    "l6_04_merge_tres_conjuntos": {
        "construcciones": ["DATA STEP", "MERGE", "BY", "TRES CONJUNTOS"],
        "entradas": {
            "CAFE": (["id", "cafe"], [(1, "latte"), (2, "espresso"), (2, "mocha")]),
            "SNACK": (["id", "snack"], [(1, "cookie"), (1, "bagel"), (2, "pie")]),
            "VENDING": (["id", "bebida"], [(1, "cola"), (2, "agua"), (2, "jugo")]),
        },
        "calculo": _calc_tres,
        "columnas": ["id", "cafe", "snack", "bebida"],
        "salida": "CONSUMO",
        "fuentes": [URL_MERGE, URL_MUCHOS_A_MUCHOS],
        "invariantes": ["filas(CONSUMO) == 4"],
        "razonamiento": (
            "Filas por grupo = máximo de los tres conjuntos: 2 en id 1 y 2 en id 2, total 4 "
            "(regla de MERGE)."
        ),
    },
    "l6_05_last_una_fila_por_grupo": {
        "construcciones": ["DATA STEP", "LAST.", "BY"],
        "entradas": {
            "VENTAS": (
                ["CIUDAD", "MONTO"],
                [
                    ("Lima", 10),
                    ("Lima", 20),
                    ("Puebla", 5),
                    ("Quito", 7),
                    ("Quito", 8),
                    ("Quito", 9),
                ],
            ),
        },
        "calculo": _calc_ultima,
        "columnas": ["CIUDAD", "MONTO"],
        "salida": "ULTIMA_VENTA",
        "fuentes": [URL_BY_GROUPS],
        "invariantes": ["filas(ULTIMA_VENTA) == 3", "suma(ULTIMA_VENTA.MONTO) == 34"],
        "razonamiento": (
            "IF LAST.CIUDAD conserva una fila por ciudad (procesamiento BY documentado)."
        ),
    },
    "l6_06_first_reinicia_acumulado": {
        "construcciones": ["DATA STEP", "FIRST.", "BY", "ACUMULADO"],
        "entradas": {
            "PAGOS_DEPTO": (
                ["DEPTO", "PAGO"],
                [("A", 5), ("A", 10), ("A", 15), ("B", 2), ("B", 3)],
            ),
        },
        "calculo": _calc_acumulado,
        "columnas": ["DEPTO", "PAGO", "ACUM"],
        "salida": "PAGOS_ACUMULADOS",
        "fuentes": [URL_BY_GROUPS],
        "invariantes": ["filas(PAGOS_ACUMULADOS) == 5", "suma(PAGOS_ACUMULADOS.ACUM) == 57"],
        "pendiente_revision": True,
        "razonamiento": (
            "El reinicio con FIRST. viene documentado; la retención de la sentencia suma "
            "(ACUM+PAGO) no se consultó en la documentación. Revisar antes de dar por verificado."
        ),
    },
    "l6_07_retain_contador": {
        "construcciones": ["DATA STEP", "RETAIN", "FIRST.", "BY"],
        "entradas": {
            "EMPLEADOS": (["DEPTO", "NOMBRE"], [("A", "Ana"), ("A", "Bruno"), ("B", "Carla")]),
        },
        "calculo": _calc_retain,
        "columnas": ["DEPTO", "NOMBRE", "CONTADOR"],
        "salida": "EMPLEADOS_NUMERADOS",
        "fuentes": [URL_BY_GROUPS],
        "invariantes": ["filas(EMPLEADOS_NUMERADOS) == 3"],
        "pendiente_revision": True,
        "razonamiento": (
            "RETAIN CONTADOR 0 con reinicio por grupo. La página de RETAIN no se pudo consultar; "
            "la regla es la del procesamiento BY y la conservación entre iteraciones."
        ),
    },
    "l6_08_nodupkey_llave": {
        "construcciones": ["PROC SORT", "NODUPKEY", "DUPLICADOS POR LLAVE"],
        "entradas": {
            "CLIENTES_DUP": (
                ["ID", "TEXTO"],
                [(3, "c1"), (1, "a1"), (3, "c2"), (2, "b1"), (1, "a2")],
            ),
        },
        "calculo": _calc_nodupkey,
        "columnas": ["ID", "TEXTO"],
        "salida": "CLIENTES_UNICOS",
        "fuentes": [_URL_SORT],
        "invariantes": ["filas(CLIENTES_UNICOS) == 3"],
        "pendiente_revision": True,
        "razonamiento": (
            "Quita llaves repetidas. Cuál fila se conserva (la primera en el orden de entrada) "
            "viene de fuentes secundarias; la documentación de PROC SORT consultada no lo dice."
        ),
    },
    "l6_09_nodup_registros_identicos": {
        "construcciones": ["PROC SORT", "NODUP", "BY _ALL_"],
        "entradas": {
            "VENTAS_DUP": (
                ["ID", "TEXTO", "MONTO"],
                [(1, "A", 10), (1, "A", 10), (1, "A", 20), (2, "B", 5), (2, "B", 5)],
            ),
        },
        "calculo": _calc_nodup,
        "columnas": ["ID", "TEXTO", "MONTO"],
        "salida": "VENTAS_SIN_REPETIR",
        "fuentes": [_URL_SORT],
        "invariantes": ["filas(VENTAS_SIN_REPETIR) == 3"],
        "pendiente_revision": True,
        "razonamiento": (
            "NODUP quita registros idénticos; con BY _ALL_ las idénticas quedan juntas. La regla "
            "viene de fuentes secundarias (listendata y foros), no de la documentación oficial."
        ),
    },
    "l6_10_ultimo_por_llave": {
        "construcciones": ["DATA STEP", "LAST.", "BY", "DUPLICADOS POR LLAVE"],
        "entradas": {
            "MOVIMIENTOS": (["ID", "MONTO"], [(1, 10), (1, 30), (2, 5), (3, 7), (3, 8)]),
        },
        "calculo": _calc_ultimo_por_llave,
        "columnas": ["ID", "MONTO"],
        "salida": "SALDO_FINAL",
        "fuentes": [URL_BY_GROUPS],
        "invariantes": ["filas(SALDO_FINAL) == 3", "suma(SALDO_FINAL.MONTO) == 43"],
        "razonamiento": "IF LAST.ID sobre entrada ordenada (procesamiento BY documentado).",
    },
    "l6_11_merge_mas_acumulado": {
        "construcciones": ["DATA STEP", "MERGE", "BY", "ACUMULADO"],
        "entradas": {
            "ZONAS": (["ZONA", "NOMBRE"], [("N", "Norte"), ("S", "Sur")]),
            "VENTAS": (["ZONA", "MONTO"], [("N", 10), ("N", 15), ("S", 7)]),
        },
        "calculo": _calc_merge_acumulado,
        "columnas": ["ZONA", "NOMBRE", "MONTO", "ACUM"],
        "salida": "VENTAS_ZONA",
        "fuentes": [URL_MERGE, URL_BY_GROUPS],
        "invariantes": ["filas(VENTAS_ZONA) == 3", "suma(VENTAS_ZONA.ACUM) == 42"],
        "pendiente_revision": True,
        "razonamiento": (
            "Combina dos reglas: la fila de MERGE (ZONAS aporta NOMBRE a sus dos filas) y el "
            "acumulado con la sentencia suma, cuya retención no se consultó."
        ),
    },
    "l6_12_ordenar_antes_de_merge": {
        "construcciones": ["PROC SORT", "DATA STEP", "MERGE", "BY"],
        "entradas": {
            "NOMBRES": (["ID", "NOMBRE"], [(3, "c"), (1, "a"), (2, "b")]),
            "SALDOS": (["ID", "SALDO"], [(2, 20), (3, 30), (1, 10)]),
        },
        "calculo": _calc_ordenar_merge,
        "columnas": ["ID", "NOMBRE", "SALDO"],
        "salida": "NOMBRES_CON_SALDO",
        "fuentes": [URL_MERGE, _URL_SORT],
        "invariantes": ["filas(NOMBRES_CON_SALDO) == 3", "suma(NOMBRES_CON_SALDO.SALDO) == 60"],
        "razonamiento": "MERGE exige entradas ordenadas: PROC SORT primero, como en el original.",
    },
    "l6_13_output_multiple_destinos": {
        "construcciones": ["DATA STEP", "OUTPUT múltiple", "IF/ELSE"],
        "entradas": {
            "REGISTROS": (
                ["ID", "VALOR"],
                [("a", 1), ("b", 2), ("c", 3), ("d", 4)],
            ),
        },
        "calculo_salidas": _calc_output_multiple,
        "columnas": ["ID", "VALOR"],
        "salidas": ["SALIDA_BAJA", "COPIA_BAJA", "SALIDA_ALTA"],
        "fuentes": [URL_OUTPUT],
        "invariantes": [
            "filas(SALIDA_BAJA) == 2",
            "filas(COPIA_BAJA) == 2",
            "filas(SALIDA_ALTA) == 2",
        ],
        "razonamiento": (
            "El IF/ELSE enruta cada observación a destinos explícitos; la rama THEN escribe en dos "
            "datasets. Referencia: lestmtsref, pp. 273–274."
        ),
    },
}
