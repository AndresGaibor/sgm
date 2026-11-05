"""Casos L8 de totales, segunda mitad: conciliación, periodo, Impala y cadena completa.

Los casos 01 a 04 están en `totales.py`. Este archivo se separó para respetar el límite de 300
líneas por archivo; usa las mismas piezas de `totales_base.py` y el esperado de
`totales_esperado_b.py`.
"""

from __future__ import annotations

import random
from collections import Counter
from decimal import Decimal

from totales_base import (
    COLUMNAS,
    FECHA,
    FUENTES_SAS,
    TIPOS_VALIDOS,
    base,
    caso,
    csv_bytes,
    fecha_xlsx,
    saldo,
    suma,
)
from totales_esperado_b import (
    esperado_05,
    esperado_06,
    esperado_07,
    esperado_08,
    redondear_a_centavo,
)

Caso = tuple[dict[str, bytes], dict, dict[str, tuple]]


def _es_valida(f: dict) -> bool:
    return f["TIPO_DOC"] in TIPOS_VALIDOS and f["NRO_CTA"] != ""


def _es_rechazada(f: dict) -> bool:
    return f["TIPO_DOC"] not in TIPOS_VALIDOS and f["TIPO_DOC"] != ""


def _conciliar(filas: list[dict], prefijo: str) -> dict:
    """Clasifica las filas como en 05: válidas, rechazadas y perdidas. Concilia si saldo y filas."""
    validas = [f for f in filas if _es_valida(f)]
    rechazadas = [f for f in filas if _es_rechazada(f)]
    perdidas = [f for f in filas if not _es_valida(f) and not _es_rechazada(f)]
    dif_filas = len(filas) - len(validas) - len(rechazadas)
    diferencia = redondear_a_centavo(
        Decimal(suma(filas)) - (Decimal(suma(validas)) + Decimal(suma(rechazadas)))
    )  # fmt: skip
    concilia = abs(diferencia) <= Decimal("0.01") and dif_filas == 0
    return {
        f"{prefijo}_filas_origen": len(filas),
        f"{prefijo}_filas_validas": len(validas),
        f"{prefijo}_filas_rechazadas": len(rechazadas),
        f"{prefijo}_filas_perdidas": len(perdidas),
        f"{prefijo}_diferencia_filas": dif_filas,
        f"{prefijo}_suma_saldo_origen": suma(filas),
        f"{prefijo}_diferencia_saldo": f"{diferencia:.2f}",
        f"{prefijo}_estado": "CONCILIA" if concilia else "NO CONCILIA",
    }


def caso_05(rng: random.Random) -> Caso:
    """Conciliación origen contra válidos más rechazados: CTE concilia, AHO no (planteado)."""
    cte = [base("CTE", i, saldo(rng)) for i in range(1, 46)]
    cte += [base("CTE", i, saldo(rng), TIPO_DOC="XX") for i in range(46, 51)]
    aho = [base("AHO", i, saldo(rng)) for i in range(1, 41)]
    aho += [base("AHO", i, saldo(rng), TIPO_DOC="XX") for i in range(41, 45)]
    aho.append(base("AHO", 45, "5.00", NRO_CTA=""))  # fila perdida: ni válida ni rechazada
    anomalias = {"tolerancia": "0.01", **_conciliar(cte, "cte"), **_conciliar(aho, "aho")}
    entradas = {"entradas/origen_cte.csv": csv_bytes(cte),
                "entradas/origen_aho.csv": csv_bytes(aho)}  # fmt: skip
    return entradas, caso(
        "05_conciliacion", "conciliación origen contra válidos más rechazados",
        ["macrovariable por SELECT INTO", "%IF %THEN %ELSE en macro", "%PUT NOTE",
         "PROC SQL con varias tablas en FROM (producto cartesiano de un registro)"],
        ["CTE", "AHO"], anomalias_plantadas=anomalias,
        supuestos=["tolerancia 0.01 en saldo: supuesto del caso, pendiente con el equipo",
                   "rechazada = TIPO_DOC fuera de CC, TI, CE, PA y no vacío"],
        fuentes_url=FUENTES_SAS,
    ), esperado_05(cte, aho)  # fmt: skip


def caso_06(rng: random.Random) -> Caso:
    """Periodo: ANIO, MES y DIA desde el Excel, Z2 para el mes, nombre de archivo con fecha."""
    aho = [base("AHO", i, saldo(rng), MES_PROCESO="09" if i <= 3 else "08") for i in range(1, 6)]
    anomalias = {
        "filas_origen": len(aho),
        "filas_del_periodo": sum(1 for f in aho if f["MES_PROCESO"] == "09"),
        "anio": str(FECHA["ANIO"]),
        "mes_texto": f"{FECHA['MES']:02d}",
        "dia_texto": f"{FECHA['DIA']:02d}",
        "fecha_concatenada": f"{FECHA['ANIO']}{FECHA['MES']:02d}{FECHA['DIA']:02d}",
        "archivo_salida": f"RESULTADO_AHO_{FECHA['ANIO']}{FECHA['MES']:02d}{FECHA['DIA']:02d}.csv",
    }
    entradas = {"entradas/origen_aho.csv": csv_bytes(aho),
                "entradas/Validacion_fecha.xlsx": fecha_xlsx()}  # fmt: skip
    return entradas, caso(
        "06_periodo_fecha", "periodo y fecha de validación",
        ["SELECT ... INTO :macro", "put(MES, Z2.)", "concatenación &ANIO.&MES.&DIA.",
         "nombre de archivo de salida con macrovariables", "PROC IMPORT EXCELCS"],
        ["AHO"], anomalias_plantadas=anomalias,
        supuestos=["el periodo sale del Excel, no de Impala; el DIA se usa solo para el nombre"],
        fuentes_url=FUENTES_SAS,
    ), esperado_06(aho, FECHA["ANIO"], FECHA["MES"], FECHA["DIA"])  # fmt: skip


def _maestro(rng: random.Random) -> tuple[list[dict], list[dict]]:
    """Tabla maestra de clientes (13 filas, 3 días) y tabla MCDQ de cuatro filas."""
    maestro = []
    cuenta = 0
    for dia, mes, n in (("2026-09-28", 9, 6), ("2026-09-27", 9, 4), ("2026-08-31", 8, 3)):
        for _k in range(n):
            cuenta += 1
            maestro.append({
                "YEAR": "2026", "MONTH": str(mes), "ingestion_day": dia,
                "cod_tipo_doc": "CC", "num_doc": f"SIM{cuenta:05d}",
                "nombre_cli": f"SIM CLIENTE {cuenta:03d}",
            })  # fmt: skip
    mcdq = [dict(f) for f in maestro if f["ingestion_day"] == "2026-09-28"][:4]
    return maestro, mcdq


def _csv_con_cabecera(filas: list[dict], columnas: list[str]) -> bytes:
    lineas = [";".join(columnas)] + [";".join(f[c] for c in columnas) for f in filas]
    return ("\n".join(lineas) + "\n").encode("utf-8")


DDL_IMPALA = """-- Tablas de Impala simuladas para el caso 07. Se cargan en un Impala de contenedor
-- con los CSV de esta carpeta (cabecera, separador ;). Nombres como en el original.
CREATE TABLE resultados_vspc_clientes.master_customer_data (
  YEAR INT,
  MONTH INT,
  ingestion_day STRING,
  cod_tipo_doc STRING,
  num_doc STRING,
  nombre_cli STRING
) STORED AS PARQUET;

CREATE TABLE proceso_vspc_finanzas.mcdq (
  cod_tipo_doc STRING,
  num_doc STRING,
  nombre_cli STRING,
  ingestion_day STRING
) STORED AS PARQUET;
"""


def caso_07(rng: random.Random) -> Caso:
    """Lectura simulada de Impala: último día de ingestión y pass-through a WORK."""
    maestro, mcdq = _maestro(rng)
    ultimo = [f for f in maestro if f["ingestion_day"] == "2026-09-28" and f["MONTH"] == "9"]
    anomalias = {
        "filas_master_customer_data": len(maestro),
        "maxdia_para_anio_2026_mes_9": "2026-09-28",
        "filas_ultimo_dia": len(ultimo),
        "filas_mcdq": len(mcdq),
        "filas_mcdq_ultimo_dia": sum(1 for f in mcdq if f["ingestion_day"] == "2026-09-28"),
    }
    entradas = {
        "entradas/master_customer_data.csv": _csv_con_cabecera(
            maestro, ["YEAR", "MONTH", "ingestion_day", "cod_tipo_doc", "num_doc", "nombre_cli"]
        ),
        "entradas/mcdq.csv": _csv_con_cabecera(
            mcdq, ["cod_tipo_doc", "num_doc", "nombre_cli", "ingestion_day"]
        ),
        "entradas/ddl.sql": DDL_IMPALA.encode("utf-8"),
    }  # fmt: skip
    return entradas, caso(
        "07_impala_lectura", "lectura de Impala simulada con última fecha",
        ["PROC SQL connect to IMPALA (DSN = IMPALAP)", "create table ... as select * from "
         "connection to IMPALA (...)", "disconnect from IMPALA", "SELECT ... INTO :macro",
         "connect to IMPALA (DSN = IMPALAP) sin escritura"],
        [], anomalias_plantadas=anomalias,
        supuestos=["el DSN IMPALAP es el del original; el contenedor de prueba lo define el "
                   "equipo, no el SAS", "los CSV son la carga de prueba, no datos reales"],
        fuentes_url=FUENTES_SAS,
    ), esperado_07(maestro, mcdq)  # fmt: skip


def caso_08(rng: random.Random) -> Caso:
    """Cadena completa para CTE y AHO con macro por producto: dedupe, correcciones, sábana."""
    entradas: dict[str, bytes] = {"entradas/Validacion_fecha.xlsx": fecha_xlsx()}
    anomalias: dict = {"fecha_concatenada": "20260930"}
    filas_por_producto: dict[str, list[dict]] = {}
    for prod in ("CTE", "AHO"):
        filas = [base(prod, i, saldo(rng)) for i in range(1, 31)]
        filas += [dict(filas[1]), dict(filas[3])]  # dos copias exactas
        filas[4]["TIPO_DOC"] = "CEDULA"  # corregible
        filas[8]["TIPO_CTA"] = "09"  # por corregir
        unicas = [f for f in filas[:30]]
        por_corregir = [f for f in unicas if f["TIPO_CTA"] not in ("01", "02", "03")]
        sabana = [f for f in unicas if f not in por_corregir]
        exactas = Counter(tuple(f[c] for c in COLUMNAS) for f in filas)
        extra = sum(n - 1 for n in exactas.values() if n > 1)
        n_origen = len(filas)
        # Misma fórmula que el programa: NRO_ORIGEN - (NRO_SABANA + POR_CORREGIR + extras).
        dif_total = n_origen - (len(sabana) + len(por_corregir) + (n_origen - len(unicas)))
        clave = prod.lower()
        anomalias.update({
            f"{clave}_filas_origen": n_origen,
            f"{clave}_duplicados_extra": extra,
            f"{clave}_filas_tras_dedup": len(unicas),
            f"{clave}_corregidas": 1,
            f"{clave}_por_corregir": len(por_corregir),
            f"{clave}_filas_sabana": len(sabana),
            f"{clave}_suma_saldo_sabana": suma(sabana),
            f"{clave}_dif_sin_duplicados_exactos": n_origen - (len(unicas) + len(por_corregir)),
            f"{clave}_estado": "CONCILIA" if abs(dif_total) <= 0.01 else "NO CONCILIA",
            f"{clave}_archivo_salida": f"CIERRE_{prod}_20260930.csv",
        })  # fmt: skip
        entradas[f"entradas/origen_{clave}.csv"] = csv_bytes(filas)
        filas_por_producto[prod] = filas
    return entradas, caso(
        "08_cadena_completa_macros", "cadena completa de duplicados a conciliación con macros",
        ["%macro con parámetros por producto", "PROC SORT NODUPREC", "CASE / sustitución",
         "OUTER UNION CORR", "PROC EXPORT por producto", "macrovariable de fecha"],
        ["CTE", "AHO"], anomalias_plantadas=anomalias,
        supuestos=["la cadena deduplica antes de corregir, como en el original"],
        fuentes_url=FUENTES_SAS,
    ), esperado_08(filas_por_producto["CTE"], filas_por_producto["AHO"])  # fmt: skip
