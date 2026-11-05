"""Esperado por construcción de los casos L8 de totales 01 a 04.

Cada `esperado_NN` recibe las filas plantadas por el generador y devuelve las tablas que el
programa SAS escribe, con el nombre de `salidas_esperadas` y el orden de columnas de su `SELECT`.
Sigue el programa, no una regla ideal: por ejemplo, la sabana de 02 excluye por NRO_CTA y no por
la llave completa, porque así está escrito el LEFT JOIN del original.
"""

from __future__ import annotations

from collections import Counter

from totales_base import COLUMNAS
from totales_sas import con_form, primera_por_llave, sin_duplicados_exactos, suma, tabla

LLAVE = ["RELACION", "TIPO_CTA", "NRO_CTA", "TIPO_DOC", "NRO_DOC"]
COLUMNAS_FORM = [*COLUMNAS, "FORM_FIN_SALDO_CTA"]
SALIDA_SABANA_19 = [
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
    "VAL_CRED_MES", "NRO_CRED_MES", "PROM_CRED_MES", "MED_CRED_MES", "VAL_DEB_MES",
    "NRO_DEB_MES", "PROM_DEB_MES", "MED_SALDO_CTA", "PROM_SALDO_CTA", "MAX_SALDO_CTA",
    "MIN_SALDO_CTA", "FORM_FIN_SALDO_CTA",
]  # fmt: skip


def esperado_01(filas: list[dict[str, str]]) -> dict[str, tuple]:
    """Duplicados: frecuencias por llave, NODUPKEY, NODUPREC y los conteos de control."""
    origen = con_form(filas)
    frecuencia = Counter(tuple(f[c] for c in LLAVE) for f in filas)
    grupos = sorted((k, n) for k, n in frecuencia.items() if n > 1)
    cols_frec = ["FRECUENCIA", *LLAVE]
    cols_filtro = [*LLAVE, "FRECUENCIA"]
    unicos = primera_por_llave(origen, LLAVE)
    exactos = sin_duplicados_exactos(origen, COLUMNAS_FORM)
    cuenta = [max(n - 2, 0) for _, n in grupos]
    # ORDER BY NRO_CTA del programa: la revisión sale ordenada por cuenta, no por la llave.
    revision = sorted(
        ({**dict(zip(LLAVE, k, strict=True)), "VECES": n} for k, n in grupos),
        key=lambda r: r["NRO_CTA"],
    )
    llaves_unicas = len(frecuencia)
    return {
        "FRECUENCIA_REGISTROS_AHO": (cols_frec, [[n, *k] for k, n in grupos]),
        "FILTRO_DUPLICADOS_AHO": (cols_filtro, [[*k, n] for k, n in grupos]),
        "CONCILIACION_DUPLICADOS_AHO": (
            ["FRECUENCIA", "CUENTA"],
            [[n, c] for (_, n), c in zip(grupos, cuenta, strict=True)],
        ),
        "AHO_UNICOS": tabla(COLUMNAS_FORM, unicos),
        "AHO_SIN_DUPLICADOS_EXACTOS": tabla(COLUMNAS_FORM, exactos),
        "REVISION_LLAVES_AHO": (
            [*LLAVE, "VECES"],
            [[r[c] for c in LLAVE] + [r["VECES"]] for r in revision],
        ),
        "CONTROL_DUPLICADOS_AHO": (
            ["NRO_REGISTROS_ORIGEN", "NRO_REGISTROS_SIN_EXACTOS", "NRO_LLAVES_UNICAS",
             "NRO_REGISTROS_DUPLICADOS"],
            [[len(origen), len(exactos), llaves_unicas, sum(cuenta)]],
        ),
        "SUMA_SALDO_ORIGEN_AHO": (["SUMA_SALDO_ORIGEN"], [[suma(origen)]]),
    }  # fmt: skip


def marcar(origen: list[dict]) -> list[dict]:
    """DATA step MARCA_AHO de 02: gana la primera inconsistencia; solo lo sano se corrige."""
    marcadas = []
    for fila in origen:
        g = dict(fila)
        inconsistencia, corregida = "", "NO"
        if g["TIPO_CTA"] not in ("01", "02", "03"):
            inconsistencia = "TIPO_CTA_INVALIDO"
        elif g["GMF"] not in ("S", "N"):
            inconsistencia = "GMF_INVALIDO"
        elif g["NRO_CTA"] == "":
            inconsistencia = "NRO_CTA_VACIO"
        if inconsistencia == "":
            if g["TIPO_DOC"] == "CEDULA":
                g["TIPO_DOC"], corregida = "CC", "SI"
            if g["NRO_DOC"] == "":
                g["NRO_DOC"], corregida = "0", "SI"
        g["INCONSISTENCIA"], g["CORREGIDA"] = inconsistencia, corregida
        marcadas.append(g)
    return marcadas


def esperado_02(filas: list[dict[str, str]]) -> dict[str, tuple]:
    """Inconsistencias: correcciones, por corregir (OUTER UNION CORR) y sábana por NRO_CTA."""
    marca = marcar(con_form(filas))
    cols_marca = [*COLUMNAS_FORM, "INCONSISTENCIA", "CORREGIDA"]
    por_corregir = [f for f in marca if f["INCONSISTENCIA"] != ""]  # el orden de las uniones
    corregidas = [f for f in marca if f["CORREGIDA"] == "SI"]
    # El LEFT JOIN empareja por NRO_CTA. Una clave vacía en la derecha es faltante para SAS, y
    # `INCONS_DEP_AHO.NRO_CTA IS MISSING` la deja pasar: esa fila vuelve a la sábana.
    nros_excluidos = {f["NRO_CTA"] for f in por_corregir if f["NRO_CTA"] != ""}
    sabana = [f for f in marca if f["NRO_CTA"] not in nros_excluidos]
    cols_sabana = ["RELACION", "TIPO_CTA", "NRO_CTA", "TIPO_DOC", "NRO_DOC", "GMF",
                   "FORM_FIN_SALDO_CTA", "CORREGIDA"]  # fmt: skip
    return {
        "INCONS_DEP_CORREGIDA_AHO": tabla(cols_marca, corregidas),
        "INCONS_DEP_AHO": tabla(cols_marca, por_corregir),
        "INCONS_DEP_AHO.csv": tabla(cols_marca, por_corregir),  # PROC EXPORT del mismo dataset
        "SABANA_FINAL_AHO": tabla(cols_sabana, sabana),
        "CONTROL_INCONS_AHO": (
            ["NRO_REGISTROS_INCONS_CORREGIDOS", "NRO_INCONS_POR_CORREGIR", "NRO_REG_SABANA_FINAL"],
            [[len(corregidas), len(por_corregir), len(sabana)]],
        ),
        "SUMA_SABANA_AHO": (["SUMA_SALDO_SABANA_FINAL"], [[suma(sabana)]]),
        "SUMA_CORREGIDAS_AHO": (["SUMA_SALDO_CORREGIDAS"], [[suma(corregidas)]]),
    }  # fmt: skip


def esperado_03(filas: list[dict[str, str]]) -> dict[str, tuple]:
    """Sábana nacional y extranjera: sin cuenta fuera, ORDER BY NRO_CTA, dos PROC EXPORT."""
    origen = con_form(filas)
    validas = [f for f in origen if f["NRO_CTA"] != ""]
    nal = sorted((f for f in validas if f["TIPO_DOC"] not in ("PA", "CE")),
                 key=lambda f: f["NRO_CTA"])  # fmt: skip
    ext = sorted((f for f in validas if f["TIPO_DOC"] in ("PA", "CE")),
                 key=lambda f: f["NRO_CTA"])  # fmt: skip
    sin_cuenta = [f for f in origen if f["NRO_CTA"] == ""]
    return {
        "SABANA_NAL_AHO": tabla(SALIDA_SABANA_19, nal),
        "SABANA_EXT_AHO": tabla(SALIDA_SABANA_19, ext),
        "RESULTADO_AHO_NAL.csv": tabla(SALIDA_SABANA_19, nal),
        "RESULTADO_AHO_EXT.csv": tabla(SALIDA_SABANA_19, ext),
        "CONTROL_SABANA_AHO": (
            ["NRO_RESULTADO_NAL", "NRO_RESULTADO_EXT", "NRO_FILAS_SIN_CUENTA"],
            [[len(nal), len(ext), len(sin_cuenta)]],
        ),
        "SUMA_NAL_AHO": (["SUMA_SALDO_NAL"], [[suma(nal)]]),
        "SUMA_EXT_AHO": (["SUMA_SALDO_EXT"], [[suma(ext)]]),
    }  # fmt: skip


def esperado_04(cte: list[dict[str, str]], aho: list[dict[str, str]]) -> dict[str, tuple]:
    """Totales de origen y de salida (sin TIPO_CTA 03) por producto, y el resumen."""
    salida: dict[str, list[dict]] = {}
    resultado: dict[str, tuple] = {}
    for prod, filas in (("CTE", cte), ("AHO", aho)):
        origen = con_form(filas)
        excluidas = [f for f in origen if f["TIPO_CTA"] != "03"]
        salida[prod] = excluidas
        no_vacios = sum(1 for f in origen if f["FORM_FIN_SALDO_CTA"] is not None)
        resultado[f"TOTAL_ORIGEN_{prod}"] = (
            ["NRO_FILAS_ORIGEN", "NRO_SALDOS_NO_VACIOS", "SUMA_SALDO_ORIGEN"],
            [[len(origen), no_vacios, suma(origen)]],
        )
        resultado[f"TOTAL_SALIDA_{prod}"] = (
            ["NRO_FILAS_SALIDA", "SUMA_SALDO_SALIDA"],
            [[len(excluidas), suma(excluidas)]],
        )
    resultado["RESUMEN_TOTALES"] = (
        ["FILAS_ORIGEN_CTE", "FILAS_SALIDA_CTE", "FILAS_ORIGEN_AHO", "FILAS_SALIDA_AHO"],
        [[len(cte), len(salida["CTE"]), len(aho), len(salida["AHO"])]],
    )
    return resultado
