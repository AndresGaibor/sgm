"""Esperado por construcción de v06: normalización de nombres y montos con espacios.

La decisión de motivo sale de la etiqueta de defecto. El `CASE` del programa se evalúa sobre el
contenido con las reglas de SAS que el caso declara (comparación con blancos finales, COMPBL y
STRIP). Las funciones de cadena que el oráculo no traduce se verifican aquí, por construcción.
"""

from __future__ import annotations

import re

from validaciones_modelo import (  # noqa: E402
    Esperado,
    Fila,
    comprobar,
    detalle,
    proyectar,
    tabla,
)

SELECT_V06 = [
    (1, "ANIO_PROCESO"), (4, "RELACION"), (7, "NRO_CTA"), (8, "LLAVE_NOMBRE"), (9, "TIPO_DOC"),
    (11, "GMF_TXT"), (12, "VAL_CRED_TXT"), (23, "FIN_SALDO_TXT"),
]  # fmt: skip
# Tras las conversiones de GMF y VAL_CRED: GMF, VAL_CRED_MES y VAL_CRED_LIMPIO se agregan al final.
COLUMNAS_SABANA = [
    "ANIO_PROCESO", "RELACION", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "VAL_CRED_TXT",
    "FIN_SALDO_TXT", "GMF", "VAL_CRED_MES", "VAL_CRED_LIMPIO",
]  # fmt: skip
COLUMNAS_NORM = [
    "RELACION", "NRO_CTA", "TIPO_DOC", "GMF", "VAL_CRED_MES", "VAL_CRED_LIMPIO",
    "FIN_SALDO_TXT", "LLAVE_NORMALIZADA",
]  # fmt: skip
MOTIVO_POR_ETIQUETA = {
    "nombre_con_espacios": "ESPACIOS EN NOMBRE",
    "nombre_con_enie": "NOMBRE CON ENIE",
    "nombre_con_tildes": "NOMBRE CON TILDES",
    "nombre_minusculas": "NOMBRE EN MINUSCULAS",
    "valor_con_espacios": "VALOR CON ESPACIOS",
    "validos": "SIN CAMBIO",
}


def _igual_sas(a: str, b: str) -> bool:
    """Comparación de caracteres de SAS: los blancos finales no cuentan."""
    return a.rstrip(" ") == b.rstrip(" ")


def _compbl_strip(texto: str) -> str:
    """`COMPBL(STRIP(x))`: quita blancos de los extremos y reduce los internos a uno."""
    return re.sub(" +", " ", texto.strip(" "))


def _llave_normalizada(llave: str) -> str:
    """`COMPBL(STRIP(UPCASE(x)))` del programa."""
    return _compbl_strip(llave.upper())


def _motivo(llave: str, valor_txt: str) -> str:
    """`CASE` del programa sobre el contenido: el primer motivo que aplique gana."""
    if not _igual_sas(llave, _compbl_strip(llave)):
        return "ESPACIOS EN NOMBRE"
    if "Ñ" in llave:
        return "NOMBRE CON ENIE"
    if "Í" in llave:
        return "NOMBRE CON TILDES"
    if not _igual_sas(llave, llave.upper()):
        return "NOMBRE EN MINUSCULAS"
    if not _igual_sas(valor_txt, valor_txt.replace(" ", "")):
        return "VALOR CON ESPACIOS"
    return "SIN CAMBIO"


def _fila_sabana(f: Fila) -> dict[str, object]:
    fila = proyectar(f, SELECT_V06)
    fila["GMF"] = f.num(11)
    fila["VAL_CRED_MES"] = f.num(12)
    fila["VAL_CRED_LIMPIO"] = f.crudo[12].replace(" ", "")
    return {c: fila[c] for c in COLUMNAS_SABANA}


def v06(spec: dict) -> Esperado:
    """Motivo por fila, normalización de la llave y conteo por motivo y suma por producto."""
    esp = Esperado()
    sumas: dict[str, int] = {}
    for p in ("CTE", "AHO"):
        sabana, norm, motivos = [], [], []
        for f in detalle(spec, p):
            fila = _fila_sabana(f)
            sabana.append(fila)
            llave = f.valor[8]
            motivo = _motivo(llave, f.crudo[12])
            comprobar(
                f, motivo == MOTIVO_POR_ETIQUETA[f.etiqueta], True,
                f"motivo {motivo} frente a la etiqueta",
            )  # fmt: skip
            motivos.append({"LLAVE_NOMBRE": llave, "MOTIVO": motivo})
            norm.append({
                "RELACION": fila["RELACION"], "NRO_CTA": fila["NRO_CTA"],
                "TIPO_DOC": fila["TIPO_DOC"], "GMF": fila["GMF"],
                "VAL_CRED_MES": fila["VAL_CRED_MES"],
                "VAL_CRED_LIMPIO": fila["VAL_CRED_LIMPIO"],
                "FIN_SALDO_TXT": fila["FIN_SALDO_TXT"],
                "LLAVE_NORMALIZADA": _llave_normalizada(llave),
            })  # fmt: skip
        esp.tablas[f"SABANA_{p}"] = tabla(COLUMNAS_SABANA, sabana)
        esp.tablas[f"SABANA_NORM_{p}"] = tabla(COLUMNAS_NORM, norm)
        esp.archivos[f"SABANA_NORM_{p}"] = esp.tablas[f"SABANA_NORM_{p}"]
        esp.tablas[f"MOTIVO_NORM_{p}"] = tabla(["LLAVE_NOMBRE", "MOTIVO"], motivos)
        cuenta: dict[str, int] = {}
        for m in motivos:
            cuenta[m["MOTIVO"]] = cuenta.get(m["MOTIVO"], 0) + 1
        esp.tablas[f"CONTEO_MOTIVO_{p}"] = tabla(
            ["MOTIVO", "NRO_FILAS"],
            [{"MOTIVO": m, "NRO_FILAS": cuenta[m]} for m in sorted(cuenta)],
        )
        # El programa filtra VAL_CRED_MES no faltante: ninguna fila de estos datos lo es.
        esp.tablas[f"SIN_FALTANTES_{p}"] = tabla(
            COLUMNAS_NORM, [r for r in norm if r["VAL_CRED_MES"] is not None]
        )
        sumas[p] = sum(r["VAL_CRED_MES"] for r in norm if r["VAL_CRED_MES"] is not None)
    esp.tablas["SUMA_VALOR_NORM"] = tabla(
        ["PRODUCTO", "SUMA_VAL_CRED"], [{"PRODUCTO": p, "SUMA_VAL_CRED": sumas[p]} for p in sumas]
    )
    return esp
