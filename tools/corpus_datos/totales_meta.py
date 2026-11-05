"""Metadatos de los casos L8 de totales: capa, estado, motivo, invariantes y observaciones.

Cada entrada de `META` se mezcla en el `caso.yaml` que escribe `totales.py`. El estado sale del
cruce con el oráculo SQL (`totales_cruce.py`): `traducible` solo si todo lo que el programa hace
con SQL coincide; `parcial` si el resto (PROC SORT, DATA step, macros, PROC EXPORT) queda solo por
construcción; `pendiente_revision` si además hay un formato de salida que no se puede comprobar
sin SAS real. Las observaciones dicen qué no se pudo verificar y por qué.
"""

from __future__ import annotations

TOLERANCIA_SUMAS = 0.005  # ruido de coma flotante; los saldos tienen dos decimales

META: dict[str, dict] = {
    "01_duplicados_frecuencias": {
        "yaml": {
            "capa": "C",
            "estado": "parcial",
            "motivo": "PROC SORT NODUPKEY y NODUPREC no los ejecuta el oráculo SQL; sus tablas "
                      "se calculan por construcción (razonamiento).",
            "razonamiento": "Las frecuencias, el filtro, la revisión de llaves y los conteos "
                            "de control son PROC SQL y se cruzaron con SQLite. NODUPKEY conserva "
                            "la primera fila de cada llave en orden de entrada; NODUPREC conserva "
                            "una fila por combinación idéntica de las 24 variables.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "valor(CONTROL_DUPLICADOS_AHO.NRO_REGISTROS_ORIGEN) == "
                "filas(AHO_SIN_DUPLICADOS_EXACTOS) + 5",
                "valor(CONTROL_DUPLICADOS_AHO.NRO_LLAVES_UNICAS) == filas(AHO_UNICOS)",
                "valor(CONTROL_DUPLICADOS_AHO.NRO_REGISTROS_DUPLICADOS) == 1",
            ],
        },
    },
    "02_inconsistencias_correccion": {
        "yaml": {
            "capa": "C",
            "estado": "pendiente_revision",
            "motivo": "OUTER UNION CORR no lo tiene SQLite; el cruce usa UNION ALL. El CSV de "
                      "PROC EXPORT depende de formatos no comprobados sin SAS.",
            "razonamiento": "Las correcciones y la sábana (LEFT JOIN por NRO_CTA) se cruzaron "
                            "con SQLite (OUTER UNION CORR se cambia por UNION ALL para el cruce); "
                            "la marca y las correcciones son el DATA step de MARCA_AHO, en Python.",
            "observacion_revision": "Hallazgo: la fila 31 tiene NRO_CTA vacío. El LEFT JOIN la "
                                    "empareja con sí misma (un faltante casa con otro faltante en "
                                    "SAS), y IS MISSING es verdadero en esa fila, así que vuelve a "
                                    "la sábana: 56 filas y no 55. Supuesto no comprobado con SAS "
                                    "real. PROC EXPORT: se asume que una celda de texto vacía sale "
                                    "sin comillas, que los números salen en formato BEST y que el "
                                    "encabezado tiene los 26 nombres. PROC IMPORT DBMS=DLM puede "
                                    "inferir tipo numérico en columnas como VAL_CRED_MES; el "
                                    "esperado asume texto tal como viene del CSV.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "filas(INCONS_DEP_AHO) + filas(SABANA_FINAL_AHO) == 61",
                "filas(INCONS_DEP_CORREGIDA_AHO) == "
                "valor(CONTROL_INCONS_AHO.NRO_REGISTROS_INCONS_CORREGIDOS)",
                "suma(SABANA_FINAL_AHO.FORM_FIN_SALDO_CTA) == "
                "valor(SUMA_SABANA_AHO.SUMA_SALDO_SABANA_FINAL)",
            ],
        },
    },
    "03_sabana_nal_ext": {
        "yaml": {
            "capa": "C",
            "estado": "pendiente_revision",
            "motivo": "La clasificación nacional o extranjera es un DATA step; el PROC EXPORT "
                      "a CSV depende de formatos no comprobados sin SAS real.",
            "razonamiento": "Los SELECT con WHERE y ORDER BY NRO_CTA se cruzaron con SQLite, "
                            "con ORIGEN_PAIS calculado en Python como lo hace el DATA step. El "
                            "cruce coincide salvo NRO_FILAS_SIN_CUENTA (ver observacion_revision).",
            "observacion_revision": "Hallazgo del oráculo: el corpus lee una celda vacía como "
                                    "NULL, y entonces NRO_CTA = '' no cuenta las filas sin "
                                    "cuenta (SQLite da 0; SAS da 4, porque el blanco es igual a "
                                    "''). Con cadena vacía el cruce coincide aquí, pero en 02 "
                                    "falla el IS MISSING. El esperado sigue SAS. Además, mismo "
                                    "supuesto de PROC EXPORT que en 02: comillas, formato BEST y "
                                    "tipo inferido por PROC IMPORT; VAL_CRED_MES y similares van "
                                    "como '0.00'.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "filas(SABANA_NAL_AHO) + filas(SABANA_EXT_AHO) + "
                "valor(CONTROL_SABANA_AHO.NRO_FILAS_SIN_CUENTA) == 50",
                "suma(SABANA_NAL_AHO.FORM_FIN_SALDO_CTA) == valor(SUMA_NAL_AHO.SUMA_SALDO_NAL)",
                "filas(RESULTADO_AHO_NAL) == valor(CONTROL_SABANA_AHO.NRO_RESULTADO_NAL)",
            ],
        },
    },
    "04_totales_origen_salida": {
        "yaml": {
            "capa": "A",
            "estado": "traducible",
            "razonamiento": "Todo el programa es PROC SQL sobre ORIGEN_CTE y ORIGEN_AHO; la "
                            "conversión input(left()) se hace antes, como DATA step, en Python.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "valor(TOTAL_ORIGEN_CTE.NRO_FILAS_ORIGEN) == "
                "valor(TOTAL_SALIDA_CTE.NRO_FILAS_SALIDA) + 1",
                "valor(TOTAL_ORIGEN_AHO.NRO_FILAS_ORIGEN) == "
                "valor(TOTAL_SALIDA_AHO.NRO_FILAS_SALIDA) + 3",
                "valor(TOTAL_ORIGEN_CTE.NRO_FILAS_ORIGEN) - "
                "valor(TOTAL_ORIGEN_CTE.NRO_SALDOS_NO_VACIOS) == 2",
                "valor(RESUMEN_TOTALES.FILAS_SALIDA_AHO) == "
                "valor(TOTAL_SALIDA_AHO.NRO_FILAS_SALIDA)",
            ],
        },
    },
    "05_conciliacion": {
        "yaml": {
            "capa": "C",
            "estado": "parcial",
            "motivo": "El oráculo no tiene INTO ni (OBS=1): las macrovariables y el estado los "
                      "resuelve el cruce, no el oráculo; el %put y las macros de mensaje no "
                      "producen tablas.",
            "razonamiento": "Los totales, las válidas y rechazadas, y la diferencia se cruzaron "
                            "con SQLite. ROUND(x, 0.01) se calcula como en SAS (múltiplo de 0.01); "
                            "SQLite no lo hace así, ver observacion_revision.",
            "observacion_revision": "Hallazgo del oráculo: traduce ROUND(x, 0.01) como round(x, "
                                    "0.01) de SQLite, que trunca el segundo argumento a entero "
                                    "(round(12.345, 0.01) da 12.0; SAS da 12.35). Con los datos "
                                    "de este caso no cambia el resultado (0 y 5), por eso el cruce "
                                    "coincide; el oráculo es incorrecto en general.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "valor(TOTALES_CONC_AHO.NRO_ORIGEN) == valor(TOTALES_CONC_AHO.NRO_VALIDOS) + "
                "valor(TOTALES_CONC_AHO.NRO_RECHAZADOS) + 1",
                "valor(CONCILIACION_AHO.DIF_SALDO) == 5",
                "valor(CONCILIACION_CTE.DIF_FILAS) == 0",
            ],
        },
        "extra": {"mensajes": ["NOTE: CONCILIACION CTE: CONCILIA",
                               "NOTE: CONCILIACION AHO: NO CONCILIA"]},
    },
    "06_periodo_fecha": {
        "yaml": {
            "capa": "C",
            "estado": "pendiente_revision",
            "motivo": "El periodo sale de SELECT INTO y PUT(...,Z2.) de un Excel; el formato de "
                      "PROC EXPORT del nombre con fecha no se comprueba sin SAS.",
            "razonamiento": "El filtro de periodo y los conteos se cruzaron con SQLite, con las "
                            "macros resueltas a mano (2026, 09, 30) a partir del Excel leído con "
                            "zipfile.",
            "observacion_revision": "Supuesto no comprobado: PROC IMPORT EXCELCS lee AÑO, MES y "
                                    "DIA como numéricos (2026, 9, 30); MES_PROCESO del CSV se "
                                    "lee como texto '09'. Si PROC IMPORT lo infiere como número, "
                                    "el filtro y el CSV de salida cambian.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "filas(RESULTADO_AHO_PERIODO) == valor(CUENTA_PERIODO_AHO.NRO_REGISTROS_PERIODO)",
                "valor(FUERA_DEL_PERIODO_AHO.NRO_FILAS_FUERA) + filas(RESULTADO_AHO_PERIODO) == 5",
                "suma(RESULTADO_AHO_PERIODO.FORM_FIN_SALDO_CTA) == "
                "valor(CUENTA_PERIODO_AHO.SUMA_SALDO_PERIODO)",
            ],
        },
    },
    "07_impala_lectura": {
        "yaml": {
            "capa": "C",
            "estado": "parcial",
            "motivo": "La conexión IMPALA y el pass-through son del motor de Impala; aquí se "
                      "emula con SQLite sobre los CSV. Los resultados salen del SELECT interior.",
            "razonamiento": "El último día (MAX de ingestion_day con YEAR 2026 y MONTH 9), los "
                            "conteos y el pass-through se calculan sobre los CSV con SQLite. La "
                            "conexión y la lectura del MAX por SELECT INTO no se ejecutan.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "valor(CONTROL_IMPALA.NRO_FILAS_ULTIMO_DIA) == filas(MCD_ULTIMO_DIA)",
                "valor(CONTROL_IMPALA.NRO_MCDQ_ULTIMO_DIA) == valor(CONTROL_IMPALA.NRO_FILAS_MCDQ)",
                "suma(MASTER_POR_MES.NRO_FILAS) == 13",
            ],
        },
    },
    "08_cadena_completa_macros": {
        "yaml": {
            "capa": "C",
            "estado": "pendiente_revision",
            "motivo": "Cadena con macro por producto, NODUPREC, PROC EXPORT y una fórmula de "
                      "conciliación que no hace lo que dice su nombre (ver observacion_revision).",
            "razonamiento": "Por producto: dedupe por construcción (NODUPREC), marca, sábana y "
                            "totales; los SQL se cruzaron con SQLite con las macros resueltas. Con "
                            "la convención de vacío del corpus el cruce falla en la sábana "
                            "(INCONSISTENCIA = ''); con cadena vacía coincide en todo.",
            "observacion_revision": "Hallazgo del oráculo: la convención de vacío como NULL rompe "
                                    "INCONSISTENCIA = '' (SABANA queda en 0 filas y arrastra "
                                    "TOTALES, CONCILIACION y RESUMEN). "
                                    "DIF_SIN_DUPLICADOS_EXACTOS resta NRO_POR_CORREGIR de "
                                    "NRO_ORIGEN - NRO_UNICOS; el nombre sugiere los duplicados "
                                    "exactos (2 por producto), pero la fórmula da 1. El esperado "
                                    "sigue la fórmula escrita. Además, el estado usa solo "
                                    "DIF_TOTAL (no las filas), a diferencia de 05.",
            "tolerancia": TOLERANCIA_SUMAS,
            "orden_relevante": False,
            "invariantes": [
                "valor(TOTALES_CTE.NRO_ORIGEN) == valor(TOTALES_CTE.NRO_UNICOS) + 2",
                "valor(TOTALES_CTE.NRO_SABANA) + valor(TOTALES_CTE.NRO_POR_CORREGIR) == "
                "valor(TOTALES_CTE.NRO_UNICOS)",
                "suma(SABANA_CTE.FORM_FIN_SALDO_CTA) == valor(TOTALES_CTE.SUMA_SABANA)",
                "valor(RESUMEN_CADENA.NRO_SABANA) == valor(TOTALES_CTE.NRO_SABANA)",
            ],
        },
    },
}
