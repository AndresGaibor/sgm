"""Esperado por construcción de v01 (tipo de documento) y v02 (documento vacío o cero).

Cada función lee las filas plantadas (`validaciones_modelo`) y aplica las decisiones del programa
SAS. La decisión sale de la etiqueta de defecto; la condición del programa se aplica al contenido
solo para comprobar que etiqueta y contenido dicen lo mismo (`comprobar`).
"""

from __future__ import annotations

from validaciones_modelo import (  # noqa: E402
    Esperado,
    Fila,
    comprobar,
    conteos,
    detalle,
    excel_codigos,
    proyectar,
    tabla,
)

# SELECT de cada programa: número de VAR y alias, en el orden del SELECT.
SELECT_V01 = [
    (1, "ANIO_PROCESO"), (2, "MES_PROCESO"), (4, "RELACION"), (6, "TIPO_CTA"), (7, "NRO_CTA"),
    (8, "LLAVE_NOMBRE"), (9, "TIPO_DOC"), (10, "NRO_DOC"), (11, "GMF"), (12, "VAL_CRED_MES"),
    (13, "NRO_CRED_MES"), (14, "PROM_CRED_MES"), (15, "MED_CRED_MES"), (16, "VAL_DEB_MES"),
    (17, "NRO_DEB_MES"), (18, "PROM_DEB_MES"), (19, "MED_SALDO_CTA"), (20, "PROM_SALDO_CTA"),
    (21, "MAX_SALDO_CTA"), (22, "MIN_SALDO_CTA"), (23, "FIN_SALDO_CTA"),
]  # fmt: skip
SELECT_V02 = [
    (1, "ANIO_PROCESO"), (2, "MES_PROCESO"), (4, "RELACION"), (6, "TIPO_CTA"), (7, "NRO_CTA"),
    (8, "LLAVE_NOMBRE"), (9, "TIPO_DOC"), (11, "GMF"), (23, "FIN_SALDO_CTA"),
]  # fmt: skip

# Columnas de v02 tras el DATA step que convierte NRO_DOC: el número se agrega al final.
COLUMNAS_SABANA_V02 = [
    "ANIO_PROCESO", "MES_PROCESO", "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC",
    "GMF", "FIN_SALDO_CTA", "NRO_DOC",
]  # fmt: skip
# Las seis columnas que los SELECT de rechazo y de validos toman de la sabana.
COLUMNAS_DOC = ["RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC"]
# Las ocho columnas del SELECT de v01 que pasan a la tabla de validos.
COLUMNAS_VALIDO_V01 = [*COLUMNAS_DOC, "GMF", "FIN_SALDO_CTA"]


def _sin_documento(f: Fila) -> bool:
    """`NRO_DOC = 0 OR NRO_DOC IS MISSING` del programa, sobre el número convertido."""
    numero = f.num(10)
    return numero is None or numero == 0


def v01(spec: dict, excel: dict) -> Esperado:
    """Tipo de documento contra la homologación: el programa separa validos y rechazados."""
    esp = Esperado()
    homol = excel_codigos(excel, "homol_tipo_doc")
    invalidos: dict[str, list[dict]] = {}
    validos: dict[str, list[dict]] = {}
    for producto in ("CTE", "AHO"):
        inv, val, sab = [], [], []
        for f in detalle(spec, producto):
            fila = proyectar(f, SELECT_V01)
            sab.append(fila)
            es_invalido = f.etiqueta == "tipo_doc_invalido"
            comprobar(f, f.valor[9] not in homol, es_invalido, "TIPO_DOC fuera de homologación")
            (inv if es_invalido else val).append(fila)
        invalidos[producto], validos[producto] = inv, val
        esp.tablas[f"SABANA_{producto}"] = tabla([a for _, a in SELECT_V01], sab)
        esp.tablas[f"TIPO_DOC_INVALIDO_{producto}"] = tabla(COLUMNAS_DOC, inv)
        esp.tablas[f"TIPO_DOC_VALIDO_{producto}"] = tabla(COLUMNAS_VALIDO_V01, val)
        rechazo = [{**r, "INCONSISTENCIA": "TIPO DOC INVALIDO"} for r in inv]
        rechazo_cols = [*COLUMNAS_DOC, "INCONSISTENCIA"]
        esp.tablas[f"RECHAZO_TIPO_DOC_{producto}"] = tabla(rechazo_cols, rechazo)
        esp.archivos[f"RECHAZO_TIPO_DOC_{producto}"] = esp.tablas[f"RECHAZO_TIPO_DOC_{producto}"]
    esp.tablas["CONTEO_RECHAZO_TIPO_DOC"] = conteos(
        "PRODUCTO", "NRO_RECHAZOS", [(p, len(invalidos[p])) for p in ("CTE", "AHO")]
    )
    esp.tablas["CONTEO_VALIDO_TIPO_DOC"] = conteos(
        "PRODUCTO", "NRO_VALIDOS", [(p, len(validos[p])) for p in ("CTE", "AHO")]
    )
    return esp


def v02(spec: dict) -> Esperado:
    """Documento vacío o cero: tit-cot y FA, y la suma del saldo de las filas válidas de CTE."""
    esp = Esperado()
    cuentas: dict[str, tuple[int, int]] = {}
    for producto in ("CTE", "AHO"):
        tit, fa, val, sab = [], [], [], []
        for f in detalle(spec, producto):
            fila = proyectar(f, SELECT_V02)
            fila["NRO_DOC"] = f.num(10)
            fila = {c: fila[c] for c in COLUMNAS_SABANA_V02}
            sab.append(fila)
            if f.etiqueta == "validos":
                comprobar(f, _sin_documento(f), False, "NRO_DOC válido")
                val.append(fila)
                continue
            comprobar(f, _sin_documento(f), True, "NRO_DOC vacío o cero")
            # El SELECT tit-cot exige RELACION <> 9902; el de FA exige RELACION = 9902.
            es_fa = f.etiqueta.startswith("fa_")
            comprobar(f, f.valor[4] == 9902, es_fa, "RELACION 9902 en FA")
            (fa if es_fa else tit).append(fila)
        esp.tablas[f"SABANA_{producto}"] = tabla(COLUMNAS_SABANA_V02, sab)
        esp.tablas[f"NRO_DOC_VACIO_0_TIT_COT_{producto}"] = tabla(COLUMNAS_DOC, tit)
        esp.tablas[f"INCONS_NRO_DOC_VACIO_0_FA_{producto}"] = tabla(COLUMNAS_DOC, fa)
        esp.tablas[f"NRO_DOC_NO_VACIO_NI_0_{producto}"] = tabla(COLUMNAS_DOC, val)
        rechazo = [{**r, "INCONSISTENCIA": "NRO DOC VACIO O CERO"} for r in [*tit, *fa]]
        rechazo_cols = [*COLUMNAS_DOC, "INCONSISTENCIA"]
        esp.tablas[f"RECHAZO_NRO_DOC_{producto}"] = tabla(rechazo_cols, rechazo)
        esp.archivos[f"RECHAZO_NRO_DOC_{producto}"] = esp.tablas[f"RECHAZO_NRO_DOC_{producto}"]
        cuentas[producto] = (len(tit), len(fa))
        if producto == "CTE":
            # El programa suma FIN_SALDO_CTA sobre NRO_DOC_NO_VACIO_NI_0_CTE, que no tiene esa
            # columna (su SELECT no la trae). En SAS la variable queda en faltante, y la suma
            # también.
            suma = None
            esp.tablas["SUMA_SALDO_CTE_VALIDAS"] = tabla(
                ["SUMA_SALDO_FINAL_CTE"], [{"SUMA_SALDO_FINAL_CTE": suma}]
            )
    esp.tablas["CONTEO_NRO_DOC_TIT_COT"] = conteos(
        "PRODUCTO", "NRO_RECHAZOS", [(p, cuentas[p][0]) for p in ("CTE", "AHO")]
    )
    esp.tablas["CONTEO_NRO_DOC_FA"] = conteos(
        "PRODUCTO", "NRO_RECHAZOS", [(p, cuentas[p][1]) for p in ("CTE", "AHO")]
    )
    return esp
