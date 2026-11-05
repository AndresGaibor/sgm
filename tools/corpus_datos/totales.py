"""Genera las entradas y los `caso.yaml` de los casos L8 de totales.

Uso: uv run python tools/corpus_datos/totales.py [carpeta_destino]

Los casos 01 a 04 están aquí; los 05 a 08 en `totales_casos_b.py`, y las piezas comunes en
`totales_base.py`. Los `programa.sas` se escriben a mano en cada carpeta y no los genera este
script. Escribe solo `entradas/` y `caso.yaml`, con semilla fija.
"""

from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

import yaml
from totales_base import COLUMNAS, DESTINO, FUENTES_SAS, SEMILLA, base, caso, csv_bytes, saldo, suma
from totales_casos_b import caso_05, caso_06, caso_07, caso_08

Caso = tuple[dict[str, bytes], dict]

Caso = tuple[dict[str, bytes], dict]  # (entradas por ruta relativa, caso.yaml)


def caso_01(rng: random.Random) -> Caso:
    """Duplicados exactos y por llave; frecuencias por cuenta (NODUPREC, NODUPKEY, HAVING)."""
    filas = [base("AHO", i, saldo(rng)) for i in range(1, 41)]
    filas += [dict(filas[i - 1]) for i in (3, 7, 11)]  # copias exactas
    filas += [dict(filas[14]), dict(filas[14])]  # la cuenta 15 aparece tres veces
    filas += [base("AHO", i, saldo(rng)) for i in (20, 21)]  # misma llave, otro saldo
    llaves = Counter((f["RELACION"], f["TIPO_CTA"], f["NRO_CTA"], f["TIPO_DOC"], f["NRO_DOC"])
                     for f in filas)  # fmt: skip
    exactas = Counter(tuple(f[c] for c in COLUMNAS) for f in filas)
    grupos_exactos = [n for n in exactas.values() if n > 1]
    grupos_llave = [n for n in llaves.values() if n > 1]
    anomalias = {
        "filas_origen": len(filas),
        "grupos_duplicados_exactos": len(grupos_exactos),
        "filas_extra_duplicados_exactos": sum(n - 1 for n in grupos_exactos),
        "grupos_duplicados_por_llave": len(grupos_llave),
        "filas_extra_por_llave": sum(n - 1 for n in grupos_llave),
        "llaves_unicas": len(llaves),
        "extra_segun_case_original": sum(n - 2 for n in grupos_llave if n > 2),
        "suma_saldo_origen": suma(filas),
    }
    entradas = {"entradas/origen_aho.csv": csv_bytes(filas)}
    salidas = {"tablas_work": ["FRECUENCIA_REGISTROS_AHO", "FILTRO_DUPLICADOS_AHO",
                               "AHO_UNICOS", "AHO_SIN_DUPLICADOS_EXACTOS"],
               "archivos": []}  # fmt: skip
    return entradas, caso(
        "01_duplicados_frecuencias", "duplicados y frecuencias",
        ["PROC SORT NODUPKEY", "PROC SORT NODUPREC", "PROC SQL GROUP BY HAVING COUNT(*)",
         "CASE WHEN en PROC SQL", "SUM sobre tabla de frecuencias"],
        ["AHO"], anomalias_plantadas=anomalias, salidas_esperadas=salidas,
        supuestos=["el NODUPKEY conserva la primera fila de cada llave (EQUALS por defecto)"],
        fuentes_url=FUENTES_SAS,
    )  # fmt: skip


def caso_02(rng: random.Random) -> Caso:
    """Inconsistencias corregibles (la SAS las arregla) y por corregir (van a INCONS_DEP_AHO)."""
    filas = [base("AHO", i, saldo(rng)) for i in range(1, 61)]
    for i in (5, 6, 7, 8):
        filas[i - 1]["TIPO_DOC"] = "CEDULA"  # corregible: se cambia a CC
    for i in (10, 11):
        filas[i - 1]["NRO_DOC"] = ""  # corregible: se pone 0
    for i in (8, 20, 21):
        filas[i - 1]["TIPO_CTA"] = "09"  # por corregir: tipo de cuenta fuera de 01, 02, 03
    filas[29]["GMF"] = "X"  # por corregir
    filas[30]["NRO_CTA"] = ""  # por corregir
    por_corregir = [i for i, f in enumerate(filas, 1)
                    if f["TIPO_CTA"] not in ("01", "02", "03") or f["GMF"] not in ("S", "N")
                    or f["NRO_CTA"] == ""]  # fmt: skip
    corregibles = [i for i, f in enumerate(filas, 1) if i not in por_corregir
                   and (f["TIPO_DOC"] == "CEDULA" or f["NRO_DOC"] == "")]  # fmt: skip
    anomalias = {
        "filas_origen": len(filas),
        "filas_corregibles": len(corregibles),
        "filas_por_corregir": len(por_corregir),
        "filas_solapadas_cedula_y_tipo_cta": 1,  # fila 8: gana por corregir, no se corrige
        "filas_sabana_final": len(filas) - len(por_corregir),
        "suma_saldo_sabana_final": suma([f for i, f in enumerate(filas, 1)
                                         if i not in por_corregir]),  # fmt: skip
    }
    entradas = {"entradas/origen_aho.csv": csv_bytes(filas)}
    salidas = {"tablas_work": ["INCONS_DEP_CORREGIDA_AHO", "INCONS_DEP_AHO", "SABANA_FINAL_AHO"],
               "archivos": ["INCONS_DEP_AHO.csv"]}  # fmt: skip
    return entradas, caso(
        "02_inconsistencias_correccion", "inconsistencias corregidas y por corregir",
        ["OUTER UNION CORR", "IS MISSING en LEFT JOIN", "sustitución condicional en DATA step",
         "PROC EXPORT a CSV"],
        ["AHO"], anomalias_plantadas=anomalias, salidas_esperadas=salidas,
        supuestos=["la precedencia es: primero por corregir; solo lo que no lo es, se corrige"],
        fuentes_url=FUENTES_SAS,
    )  # fmt: skip


def caso_03(rng: random.Random) -> Caso:
    """Sábana final nacional y extranjera con orden de columnas y dos PROC EXPORT."""
    nal = [base("AHO", i, saldo(rng), TIPO_DOC=("CC", "TI")[i % 2]) for i in range(1, 31)]
    ext = [base("AHO", i, saldo(rng), TIPO_DOC=("PA", "CE")[i % 2]) for i in range(31, 51)]
    for i in (29, 30):
        nal[i - 1]["NRO_CTA"] = ""  # sin cuenta: fuera de la sábana
    for i in (49, 50):
        ext[i - 31]["NRO_CTA"] = ""
    validas_nal = [f for f in nal if f["NRO_CTA"]]
    validas_ext = [f for f in ext if f["NRO_CTA"]]
    anomalias = {
        "filas_origen": len(nal) + len(ext),
        "filas_nal_origen": len(nal),
        "filas_ext_origen": len(ext),
        "filas_sin_cuenta": 4,
        "filas_resultado_nal": len(validas_nal),
        "filas_resultado_ext": len(validas_ext),
        "suma_saldo_resultado_nal": suma(validas_nal),
        "suma_saldo_resultado_ext": suma(validas_ext),
    }
    entradas = {"entradas/origen_aho.csv": csv_bytes(nal + ext)}
    salidas = {"tablas_work": ["SABANA_NAL_AHO", "SABANA_EXT_AHO"],
               "archivos": ["RESULTADO_AHO_NAL.csv", "RESULTADO_AHO_EXT.csv"]}  # fmt: skip
    return entradas, caso(
        "03_sabana_nal_ext", "sábana final nacional y extranjera",
        ["PROC SORT BY", "SELECT con orden de columnas", "WHERE IS NOT MISSING / NRO_CTA <> ''",
         "PROC EXPORT DBMS=CSV REPLACE", "SUM por archivo"],
        ["AHO"], anomalias_plantadas=anomalias, salidas_esperadas=salidas,
        supuestos=["extranjero = TIPO_DOC PA o CE: decisión de este caso, no del SAS"],
        fuentes_url=FUENTES_SAS,
    )  # fmt: skip


def caso_04(rng: random.Random) -> Caso:
    """Totales de origen y de salida por producto, con saldo vacío y espacios a la izquierda."""
    cte = [base("CTE", i, saldo(rng)) for i in range(1, 41)]
    for i in range(1, 6):
        cte[i - 1]["FIN_SALDO_CTA"] = "  " + cte[i - 1]["FIN_SALDO_CTA"]  # espacios a la izq.
    for i in (39, 40):
        cte[i - 1]["FIN_SALDO_CTA"] = ""  # vacío: SUM lo ignora, COUNT(*) no
    cte[37]["TIPO_CTA"] = "03"  # sale en la salida
    aho = [base("AHO", i, saldo(rng)) for i in range(1, 41)]
    for i in (38, 39, 40):
        aho[i - 1]["TIPO_CTA"] = "03"  # fuera de la salida
    salida = lambda filas: [f for f in filas if f["TIPO_CTA"] != "03"]  # noqa: E731
    anomalias = {
        "cte_filas_origen": len(cte),
        "cte_saldos_no_vacios_origen": sum(1 for f in cte if f["FIN_SALDO_CTA"].strip()),
        "cte_suma_saldo_origen": suma(cte),
        "cte_filas_salida": len(salida(cte)),
        "cte_suma_saldo_salida": suma(salida(cte)),
        "aho_filas_origen": len(aho),
        "aho_filas_salida": len(salida(aho)),
        "aho_suma_saldo_origen": suma(aho),
        "aho_suma_saldo_salida": suma(salida(aho)),
    }
    entradas = {"entradas/origen_cte.csv": csv_bytes(cte),
                "entradas/origen_aho.csv": csv_bytes(aho)}  # fmt: skip
    salidas = {"tablas_work": ["TOTAL_ORIGEN_CTE", "TOTAL_SALIDA_CTE", "TOTAL_ORIGEN_AHO",
                               "TOTAL_SALIDA_AHO"], "archivos": []}  # fmt: skip
    return entradas, caso(
        "04_totales_origen_salida", "totales de origen y de salida por producto",
        ["COUNT(*) y SUM(...) en PROC SQL", "input(left(...), 20.)", "SUM ignora faltantes",
         "WHERE TIPO_CTA <> '03'"],
        ["CTE", "AHO"], anomalias_plantadas=anomalias, salidas_esperadas=salidas,
        supuestos=["la salida excluye TIPO_CTA 03; regla de este caso, no del SAS"],
        fuentes_url=FUENTES_SAS,
    )  # fmt: skip


CASOS = (caso_01, caso_02, caso_03, caso_04, caso_05, caso_06, caso_07, caso_08)


def generar() -> dict[str, Caso]:
    """Entradas y `caso.yaml` de cada caso; el caso n usa la semilla SEMILLA + n."""
    resultado: dict[str, Caso] = {}
    for n, funcion in enumerate(CASOS, 1):
        entradas, datos = funcion(random.Random(SEMILLA + n))
        resultado[datos["id"]] = (entradas, datos)
    return resultado


def escribir(destino: Path) -> list[Path]:
    """Escribe las entradas y el caso.yaml de cada caso bajo `destino/<id>/`."""
    escritos: list[Path] = []
    for id_, (entradas, datos) in generar().items():
        carpeta = destino / id_
        for relativa, contenido in entradas.items():
            ruta = carpeta / relativa
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(contenido)
            escritos.append(ruta)
        ruta = carpeta / "caso.yaml"
        texto = yaml.safe_dump(datos, allow_unicode=True, sort_keys=False, width=100)
        ruta.write_text(texto, encoding="utf-8", newline="\n")
        escritos.append(ruta)
    return escritos


def main(argv: list[str]) -> int:
    destino = Path(argv[0]) if argv else DESTINO
    for ruta in escribir(destino):
        print(ruta)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
