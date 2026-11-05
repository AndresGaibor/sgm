"""Esperado por construcción de v05: codex inválido y saldo negativo, por producto.

Los dos rechazos son independientes entre sí: cada fila tiene a lo sumo una etiqueta, y la sabana
válida excluye las llaves que aparecen en cualquiera de los dos. Las reglas del programa se
aplican al contenido solo para comprobar la coherencia con la etiqueta.
"""

from __future__ import annotations

from validaciones_modelo import (  # noqa: E402
    Esperado,
    comprobar,
    conteos,
    detalle,
    proyectar,
    tabla,
)

CODEX_RELACION = 1000  # relación que dispara la regla de codex en el corpus
SELECT_V05 = [
    (1, "ANIO_PROCESO"), (2, "MES_PROCESO"), (4, "RELACION"), (6, "TIPO_CTA"), (7, "NRO_CTA"),
    (8, "LLAVE_NOMBRE"), (9, "TIPO_DOC"), (10, "NRO_DOC"), (11, "GMF_TXT"),
    (12, "VAL_CRED_MES"), (23, "FIN_SALDO_TXT"),
]  # fmt: skip
# Tras las dos conversiones: GMF y FIN_SALDO_CTA se agregan en ese orden y se borran los textos.
COLUMNAS_SABANA = [
    "ANIO_PROCESO", "MES_PROCESO", "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC",
    "NRO_DOC", "VAL_CRED_MES", "GMF", "FIN_SALDO_CTA",
]  # fmt: skip
COLUMNAS_RECHAZO = [
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
    "FIN_SALDO_CTA",
]  # fmt: skip
COLUMNAS_VALIDA = [
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
    "VAL_CRED_MES", "FIN_SALDO_CTA",
]  # fmt: skip


def _codex(gmf: int | None, relacion: int) -> bool:
    """`GMF NOT BETWEEN 1 AND 10 AND RELACION = 1000` del programa."""
    return (gmf is None or not 1 <= gmf <= 10) and relacion == CODEX_RELACION


def v05(spec: dict) -> Esperado:
    """Codex y saldo negativo: dos tablas de rechazo por producto y la sabana sin ninguno."""
    esp = Esperado()
    conteo_codex: dict[str, int] = {}
    conteo_saldo: dict[str, int] = {}
    for p in ("CTE", "AHO"):
        sabana, codex, saldo, valida = [], [], [], []
        for f in detalle(spec, p):
            fila = proyectar(f, SELECT_V05)
            fila["GMF"] = f.num(11)
            fila["FIN_SALDO_CTA"] = f.num(23)
            fila["VAL_CRED_MES"] = f.valor[12]
            fila = {c: fila[c] for c in COLUMNAS_SABANA}
            sabana.append(fila)
            es_codex = f.etiqueta == "codex_invalido"
            es_saldo = f.etiqueta == "saldo_negativo"
            comprobar(f, _codex(fila["GMF"], fila["RELACION"]), es_codex, "codex")
            comprobar(f, fila["FIN_SALDO_CTA"] < 0, es_saldo, "saldo negativo")
            if es_codex:
                codex.append(fila)
            elif es_saldo:
                saldo.append(fila)
            else:
                valida.append(fila)
        esp.tablas[f"SABANA_{p}"] = tabla(COLUMNAS_SABANA, sabana)
        esp.tablas[f"INCONS_CODEX_INVALIDO_{p}"] = tabla(COLUMNAS_RECHAZO, codex)
        esp.tablas[f"INCONS_SALDO_NEG_{p}"] = tabla(COLUMNAS_RECHAZO, saldo)
        esp.tablas[f"SABANA_VALIDA_{p}"] = tabla(COLUMNAS_VALIDA, valida)
        suma = sum(r["FIN_SALDO_CTA"] for r in valida)
        esp.tablas[f"SUMA_SALDO_VALIDA_{p}"] = tabla(
            [f"SUMA_SALDO_FINAL_{p}"], [{f"SUMA_SALDO_FINAL_{p}": suma}]
        )
        cols_rech = [*COLUMNAS_RECHAZO]
        rech_codex = [{**r, "INCONSISTENCIA": "CODEX INVALIDO"} for r in codex]
        rech_saldo = [{**r, "INCONSISTENCIA": "SALDO NEGATIVO"} for r in saldo]
        esp.tablas[f"RECHAZO_CODEX_{p}"] = tabla([*cols_rech, "INCONSISTENCIA"], rech_codex)
        esp.tablas[f"RECHAZO_SALDO_{p}"] = tabla([*cols_rech, "INCONSISTENCIA"], rech_saldo)
        esp.archivos[f"RECHAZO_CODEX_{p}"] = esp.tablas[f"RECHAZO_CODEX_{p}"]
        esp.archivos[f"RECHAZO_SALDO_{p}"] = esp.tablas[f"RECHAZO_SALDO_{p}"]
        conteo_codex[p], conteo_saldo[p] = len(codex), len(saldo)
    esp.tablas["CONTEO_CODEX_SALDO"] = conteos(
        "REGLA", "NRO_RECHAZOS",
        [("CTE CODEX", conteo_codex["CTE"]), ("CTE SALDO NEG", conteo_saldo["CTE"]),
         ("AHO CODEX", conteo_codex["AHO"]), ("AHO SALDO NEG", conteo_saldo["AHO"])],
    )  # fmt: skip
    return esp
