"""Esperado por construcción de los casos L8 de totales 05 a 08.

Mismo criterio que `totales_esperado.py`: cada función sigue el programa SAS, incluidas sus
fórmulas tal como están escritas. Donde el programa tiene una fórmula que no hace lo que dice su
nombre (DIF_SIN_DUPLICADOS_EXACTOS en 08), el esperado sigue la fórmula y el caso lo anota.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from totales_base import TIPOS_VALIDOS
from totales_esperado import COLUMNAS_FORM
from totales_sas import con_form, sin_duplicados_exactos, suma, tabla

Fila = dict[str, object]


def redondear_a_centavo(valor: Decimal) -> Decimal:
    """ROUND(x, 0.01) de SAS: redondea al múltiplo de 0.01 más cercano (mitad hacia arriba)."""
    cuantos = (valor / Decimal("0.01")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return cuantos * Decimal("0.01")


def _conciliacion(origen: list[Fila]) -> tuple[list[str], list[list], Decimal, int]:
    """Totales de conciliación: válidos (con cuenta) y rechazados (TIPO_DOC no vacío, no válido)."""
    validos = [f for f in origen if f["TIPO_DOC"] in TIPOS_VALIDOS and f["NRO_CTA"] != ""]
    rechazados = [f for f in origen
                  if f["TIPO_DOC"] not in TIPOS_VALIDOS and f["TIPO_DOC"] != ""]  # fmt: skip
    total = {
        "NRO_ORIGEN": len(origen), "NRO_VALIDOS": len(validos),
        "NRO_RECHAZADOS": len(rechazados), "SUMA_ORIGEN": suma(origen),
        "SUMA_VALIDOS": suma(validos), "SUMA_RECHAZADOS": suma(rechazados),
    }  # fmt: skip
    cols = list(total)
    dif_filas = total["NRO_ORIGEN"] - (total["NRO_VALIDOS"] + total["NRO_RECHAZADOS"])
    dif_saldo = redondear_a_centavo(
        total["SUMA_ORIGEN"] - (total["SUMA_VALIDOS"] + total["SUMA_RECHAZADOS"])
    )  # fmt: skip
    return cols, [list(total.values())], dif_saldo, dif_filas


def esperado_05(cte: list[Fila], aho: list[Fila]) -> dict[str, tuple]:
    """Conciliación por producto y la tabla final apilada (OUTER UNION CORR)."""
    resultado: dict[str, tuple] = {}
    final_filas = []
    for prod, filas in (("CTE", cte), ("AHO", aho)):
        origen = con_form(filas)
        cols, fila_total, dif_saldo, dif_filas = _conciliacion(origen)
        resultado[f"TOTALES_CONC_{prod}"] = (cols, fila_total)
        resultado[f"CONCILIACION_{prod}"] = (
            ["NRO_ORIGEN", "DIF_FILAS", "DIF_SALDO", "SUMA_ORIGEN"],
            [[fila_total[0][0], dif_filas, dif_saldo, fila_total[0][3]]],
        )
        final_filas.append([prod, dif_filas, dif_saldo])
    resultado["CONCILIACION_FINAL"] = (["PRODUCTO", "DIF_FILAS", "DIF_SALDO"], final_filas)
    return resultado


def esperado_06(aho: list[Fila], anio: int, mes: int, dia: int) -> dict[str, tuple]:
    """Periodo: las macros salen del Excel (AÑO, MES, DIA) y el filtro usa el texto de MES."""
    mes_txt = f"{mes:02d}"
    origen = con_form(aho)
    periodo = sorted((f for f in origen if f["ANIO_PROCESO"] == str(anio)
                      and f["MES_PROCESO"] == mes_txt),
                     key=lambda f: f["NRO_CTA"])  # fmt: skip
    cols_periodo = ["ANIO_PROCESO", "MES_PROCESO", "RELACION", "TIPO_CTA", "NRO_CTA", "TIPO_DOC",
                    "NRO_DOC", "GMF", "FORM_FIN_SALDO_CTA"]  # fmt: skip
    meses: dict[str, int] = {}
    for f in origen:
        meses[f["MES_PROCESO"]] = meses.get(f["MES_PROCESO"], 0) + 1
    return {
        "VALIDACION_FECHA": (["AÑO", "MES", "DIA"], [[anio, mes, dia]]),
        "FORMATO_TEXTO_FECHA": (["AÑO", "MES", "DIA", "MES_VIG", "DIA_VIG"],
                                [[anio, mes, dia, mes_txt, f"{dia:02d}"]]),
        "RESULTADO_AHO_PERIODO": tabla(cols_periodo, periodo),
        f"RESULTADO_AHO_{anio}{mes_txt}{dia:02d}.csv": tabla(cols_periodo, periodo),
        "CUENTA_PERIODO_AHO": (["NRO_REGISTROS_PERIODO", "SUMA_SALDO_PERIODO"],
                               [[len(periodo), suma(periodo)]]),
        "MESES_ORIGEN_AHO": (["MES_PROCESO", "NRO_FILAS"],
                             [[m, meses[m]] for m in sorted(meses)]),
        "FUERA_DEL_PERIODO_AHO": (["NRO_FILAS_FUERA"],
                                  [[sum(1 for f in origen if f["MES_PROCESO"] != mes_txt)]]),
    }  # fmt: skip


def esperado_07(maestro: list[dict], mcdq: list[dict]) -> dict[str, tuple]:
    """Lectura de Impala sobre los CSV: último día de ingestión y conteos de control."""
    en_periodo = [f for f in maestro if f["YEAR"] == "2026" and f["MONTH"] == "9"]
    maxdia = max(f["ingestion_day"] for f in en_periodo)
    cols = ["YEAR", "MONTH", "ingestion_day", "cod_tipo_doc", "num_doc", "nombre_cli"]
    ultimo = [f for f in en_periodo if f["ingestion_day"] == maxdia]
    por_tipo: dict[str, int] = {}
    for f in ultimo:
        por_tipo[f["cod_tipo_doc"]] = por_tipo.get(f["cod_tipo_doc"], 0) + 1
    por_mes: dict[str, int] = {}
    for f in maestro:
        if f["YEAR"] == "2026":
            por_mes[f["MONTH"]] = por_mes.get(f["MONTH"], 0) + 1
    mismo_dia = sum(1 for f in mcdq if f["ingestion_day"] == maxdia)
    sin_tipo = sum(1 for f in ultimo if f["cod_tipo_doc"] in ("", None))
    return {
        "MAXDIA": (["Mday"], [[maxdia]]),
        "MCD_ULTIMO_DIA": (cols, [[f[c] for c in cols] for f in ultimo]),
        "MCD_CONTEO": (["NRO_FILAS_ULTIMO_DIA"], [[len(ultimo)]]),
        "MCDQ_CONTEO": (["NRO_FILAS_MCDQ"], [[len(mcdq)]]),
        "MCDQ_MISMO_DIA": (["NRO_MCDQ_ULTIMO_DIA"], [[mismo_dia]]),
        "CONTROL_IMPALA": (["NRO_FILAS_ULTIMO_DIA", "NRO_FILAS_MCDQ", "NRO_MCDQ_ULTIMO_DIA"],
                           [[len(ultimo), len(mcdq), mismo_dia]]),
        "CLIENTES_POR_TIPO_DOC": (["cod_tipo_doc", "NRO_CLIENTES"],
                                  [[k, por_tipo[k]] for k in sorted(por_tipo)]),
        "CLIENTES_SIN_TIPO_DOC": (["NRO_SIN_TIPO_DOC"], [[sin_tipo]]),
        "MASTER_POR_MES": (["MONTH", "NRO_FILAS"], [[k, por_mes[k]] for k in sorted(por_mes)]),
    }  # fmt: skip


COLUMNAS_SABANA_08 = ["RELACION", "TIPO_CTA", "NRO_CTA", "TIPO_DOC", "NRO_DOC", "GMF",
                      "FORM_FIN_SALDO_CTA"]  # fmt: skip
COLUMNAS_MARCA_08 = [*COLUMNAS_FORM, "INCONSISTENCIA", "CORREGIDA"]


def marcar_08(unicos: list[Fila]) -> list[Fila]:
    """DATA step MARCA_<prod> de 08: solo TIPO_CTA se marca; CEDULA pasa a CC si no hay marca."""
    marca = []
    for fila in unicos:
        g = dict(fila)
        inconsistencia = "" if g["TIPO_CTA"] in ("01", "02", "03") else "TIPO_CTA_INVALIDO"
        g["CORREGIDA"] = "NO"
        if inconsistencia == "" and g["TIPO_DOC"] == "CEDULA":
            g["TIPO_DOC"], g["CORREGIDA"] = "CC", "SI"
        g["INCONSISTENCIA"] = inconsistencia
        marca.append(g)
    return marca


def _cadena(prod: str, filas: list[Fila]) -> dict[str, tuple]:
    """Una pasada de la macro procesa_producto para un producto."""
    origen = con_form(filas)
    unicos = sin_duplicados_exactos(origen, COLUMNAS_FORM)
    marca = marcar_08(unicos)
    corregidas = [f for f in marca if f["CORREGIDA"] == "SI"]
    incons = [f for f in marca if f["INCONSISTENCIA"] != ""]
    sabana = [f for f in marca if f["INCONSISTENCIA"] == ""]
    total = {
        "NRO_ORIGEN": len(origen), "NRO_UNICOS": len(unicos),
        "NRO_CORREGIDAS": len(corregidas), "NRO_POR_CORREGIR": len(incons),
        "NRO_SABANA": len(sabana), "SUMA_SABANA": suma(sabana),
    }  # fmt: skip
    n_o, n_u = total["NRO_ORIGEN"], total["NRO_UNICOS"]
    dif_sin = n_o - (n_u + total["NRO_POR_CORREGIR"])
    dif_total = n_o - (total["NRO_SABANA"] + total["NRO_POR_CORREGIR"] + (n_o - n_u))
    return {
        f"ORIGEN_{prod}": tabla(COLUMNAS_FORM, origen),
        f"SABANA_{prod}": tabla(COLUMNAS_SABANA_08, sabana),
        f"TOTALES_{prod}": (list(total), [list(total.values())]),
        f"CONCILIACION_{prod}": (
            ["DIF_SIN_DUPLICADOS_EXACTOS", "DIF_TOTAL"],
            [[dif_sin, dif_total]],
        ),
        f"CIERRE_{prod}_20260930.csv": tabla(COLUMNAS_SABANA_08, sabana),
        f"INCONS_DEP_{prod}": tabla(COLUMNAS_MARCA_08, incons),
        f"INCONS_DEP_{prod}.csv": tabla(COLUMNAS_MARCA_08, incons),
        f"CORREGIDAS_{prod}": tabla(COLUMNAS_MARCA_08, corregidas),
    }  # fmt: skip


def esperado_08(cte: list[Fila], aho: list[Fila]) -> dict[str, tuple]:
    """Cadena completa: dos pasadas de la macro y el resumen apilado (OUTER UNION CORR)."""
    resultado = {**_cadena("CTE", cte), **_cadena("AHO", aho)}
    resumen = []
    for prod in ("CTE", "AHO"):
        _, filas = resultado[f"TOTALES_{prod}"]
        resumen.append([prod, filas[0][4], filas[0][5]])
    resultado["RESUMEN_CADENA"] = (["PRODUCTO", "NRO_SABANA", "SUMA_SABANA"], resumen)
    return resultado
