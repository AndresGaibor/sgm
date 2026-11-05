"""Esperados y comparación de `v02_vacios_ceros` para el arnés de R1-04 (hito 86).

La verdad plantada sale de `esperado/` y de `caso.yaml`; nunca se calcula con la salida del Job.
Los tres flujos que escribe el `tMap` se comparan **fila por fila** (el caso declara
`orden_relevante: false`, así que se comparan como multisets), y se comprueban las invariantes y
el desglose de anomalías (vacío frente a cero) que pide el criterio de R1-04.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v02_vacios_ceros"
PRODUCTOS = ("CTE", "AHO")
MODOS = ("tit_cot", "fa", "valido")

# Esquema de las 23 columnas que `sgm talend` emite para `client_large.sas` (hito 84).
# `test_vacios_ceros_datos.py` comprueba que siga igual a `origenes_producto().columnas_comunes`.
COLUMNAS = (
    "ANIO_PROCESO", "MES_PROCESO", "VAR3", "RELACION", "VAR5", "TIPO_CTA", "NRO_CTA",
    "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF", "VAL_CRED_MES", "NRO_CRED_MES",
    "PROM_CRED_MES", "MED_CRED_MES", "VAL_DEB_MES", "NRO_DEB_MES", "PROM_DEB_MES",
    "MED_SALDO_CTA", "PROM_SALDO_CTA", "MAX_SALDO_CTA", "MIN_SALDO_CTA", "FIN_SALDO_CTA",
)
# Proyección que publican los `esperado/` del caso; el SELECT del SAS trae más columnas.
RECHAZO = ("RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC")
VALIDO = (*RECHAZO, "FIN_SALDO_CTA")
ESQUEMAS = {"tit_cot": RECHAZO, "fa": RECHAZO, "valido": VALIDO}
ARCHIVOS = {
    "tit_cot": "NRO_DOC_VACIO_0_TIT_COT_{p}.csv",
    "fa": "INCONS_NRO_DOC_VACIO_0_FA_{p}.csv",
    "valido": "NRO_DOC_NO_VACIO_NI_0_{p}.csv",
}
SALIDAS = {"tit_cot": "tit_cot.csv", "fa": "fa.csv", "valido": "validos.csv"}


def _filas(ruta: Path, con_cabecera: bool = True) -> list[tuple[str, ...]]:
    """Filas de un CSV como tuplas de texto, sin la cabecera si la tiene."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        filas = [tuple(fila) for fila in csv.reader(archivo, delimiter=",")]
    return filas[1:] if con_cabecera else filas


def esperado(producto: str) -> dict[str, list[tuple[str, ...]]]:
    """Filas esperadas de cada flujo, leídas de `esperado/`."""
    return {
        modo: _filas(CASO / "esperado" / nombre.format(p=producto))
        for modo, nombre in ARCHIVOS.items()
    }


def observado(salida: Path) -> dict[str, list[tuple[str, ...]]]:
    """Filas que escribió el Job: los tres CSV sin cabecera."""
    return {
        modo: _filas(salida / nombre, con_cabecera=False)
        for modo, nombre in SALIDAS.items()
    }


def anomalias(filas: list[tuple[str, ...]]) -> Counter:
    """Desglose vacío/cero de la columna `NRO_DOC` (índice 5 en la proyección de rechazo)."""
    return Counter(
        "vacio" if fila[5] == "" else "cero" if fila[5] == "0" else "otro" for fila in filas
    )


def anomalias_plantadas() -> dict[str, dict[str, int]]:
    """Conteos declarados en `caso.yaml`, por producto, modo y clase."""
    caso = yaml.safe_load((CASO / "caso.yaml").read_text(encoding="utf-8"))
    resultado: dict[str, dict[str, int]] = {}
    for producto in PRODUCTOS:
        datos = caso["anomalias_plantadas"][producto.lower()]
        # AHO no declara `fa_nro_doc_cero`: el caso no planta ninguna, no es un dato perdido.
        resultado[producto] = {
            "tit_cot_vacio": datos.get("tit_cot_nro_doc_vacio", 0),
            "tit_cot_cero": datos.get("tit_cot_nro_doc_cero", 0),
            "fa_vacio": datos.get("fa_nro_doc_vacio", 0),
            "fa_cero": datos.get("fa_nro_doc_cero", 0),
            "validos": datos["validos"],
        }
    return resultado


def _suma_saldo_esperada() -> int:
    filas = _filas(CASO / "esperado" / "SUMA_SALDO_CTE_VALIDAS.csv")
    return int(filas[0][0])


def _conteos(nombre: str) -> int:
    return sum(int(fila[1]) for fila in _filas(CASO / "esperado" / nombre))


def _suma_observada(filas: list[tuple[str, ...]]) -> int:
    """Suma de `FIN_SALDO_CTA` (índice 6 de la proyección de válidos)."""
    return sum(int(fila[6]) for fila in filas)


def informe(producto: str, esp: dict, obs: dict) -> bool:
    """Compara los tres flujos fila por fila y el desglose de anomalías plantadas."""
    bueno = True
    for modo in MODOS:
        e, o = sorted(esp[modo]), sorted(obs[modo])
        cuadra = e == o
        bueno &= cuadra
        print(
            f"{producto} {modo}: esperadas {len(e)} filas, obtenidas {len(o)}; "
            f"{'OK' if cuadra else 'DIFERENCIA'}"
        )
        if not cuadra:
            print(f"  solo en esperado: {sorted(Counter(e) - Counter(o))[:3]}")
            print(f"  solo en obtenido: {sorted(Counter(o) - Counter(e))[:3]}")
    pl = anomalias_plantadas()[producto]
    tit, fa = anomalias(obs["tit_cot"]), anomalias(obs["fa"])
    desglose = {
        "tit_cot_vacio": tit["vacio"], "tit_cot_cero": tit["cero"],
        "fa_vacio": fa["vacio"], "fa_cero": fa["cero"],
        "validos": len(obs["valido"]),
    }
    cuadra = desglose == pl
    bueno &= cuadra
    estado = "OK" if cuadra else "DIFERENCIA"
    print(f"{producto} anomalías plantadas {pl}; obtenidas {desglose}; {estado}")
    return bueno


def invariantes(resultados: dict[str, dict[str, list[tuple[str, ...]]]]) -> bool:
    """Las tres invariantes del `caso.yaml` que se pueden medir con los tres flujos."""
    sabana = {
        p: len(_filas(CASO / "esperado" / f"SABANA_{p}.csv")) for p in PRODUCTOS
    }
    rechazos = {
        p: len(resultados[p]["tit_cot"]) + len(resultados[p]["fa"]) for p in PRODUCTOS
    }
    uno = all(sabana[p] == len(resultados[p]["valido"]) + rechazos[p] for p in PRODUCTOS)
    dos = (
        _conteos("CONTEO_NRO_DOC_TIT_COT.csv") + _conteos("CONTEO_NRO_DOC_FA.csv")
        == sum(rechazos.values())
    )
    tres = _suma_observada(resultados["CTE"]["valido"]) == _suma_saldo_esperada()
    print(
        f"Invariantes: sábana=válidos+rechazos {'sí' if uno else 'NO'}; "
        f"conteos=rechazos CTE+AHO {'sí' if dos else 'NO'}; "
        f"suma saldo CTE={_suma_observada(resultados['CTE']['valido'])} "
        f"frente a {_suma_saldo_esperada()} {'sí' if tres else 'NO'}"
    )
    return uno and dos and tres


__all__ = [
    "ARCHIVOS", "CASO", "COLUMNAS", "ESQUEMAS", "MODOS", "PRODUCTOS", "RECHAZO", "SALIDAS",
    "VALIDO", "anomalias", "anomalias_plantadas", "esperado", "informe", "invariantes", "observado",
]
