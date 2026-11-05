"""Esperado por construcción de v04 (tipo de cuenta y GMF) y v05 (codex y saldo negativo).

v04 es secuencial: el GMF solo se evalúa sobre las filas que pasan la prueba de tipo de cuenta.
La decisión sale de la etiqueta; la condición del programa se aplica al contenido para comprobar.
"""

from __future__ import annotations

from validaciones_modelo import (  # noqa: E402
    Esperado,
    Fila,
    comprobar,
    conteos,
    detalle,
    proyectar,
    tabla,
)

TIPOS_CUENTA_VALIDOS = {1, 2, 3, 4, 5}
MOTIVO_GMF = {"gmf_invalido": "GMF NO NUMERICO", "gmf_fuera_rango": "GMF FUERA DE RANGO"}

# v04: GMF_TXT se convierte y su columna nueva va al final (GMF_TXT se borra).
SELECT_V04 = [
    (4, "RELACION"), (6, "TIPO_CTA"), (7, "NRO_CTA"), (8, "LLAVE_NOMBRE"), (9, "TIPO_DOC"),
    (10, "NRO_DOC"), (11, "GMF_TXT"), (23, "FIN_SALDO_CTA"),
]  # fmt: skip
COLUMNAS_SABANA_V04 = [
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "FIN_SALDO_CTA",
    "GMF",
]  # fmt: skip
# Los SELECT de las etapas listan GMF antes que FIN_SALDO_CTA (así lo escribe el programa).
COLUMNAS_TIPO_OK = [
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
    "FIN_SALDO_CTA",
]  # fmt: skip
COLUMNAS_TIPO_RECHAZO = [
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF",
]  # fmt: skip
COLUMNAS_GMF_RECHAZO = [*COLUMNAS_TIPO_RECHAZO, "MOTIVO"]
COLUMNAS_CUENTA = ["RELACION", "TIPO_CTA", "LLAVE_NOMBRE", "GMF", "INCONSISTENCIA"]


def _sabana_v04(f: Fila) -> dict[str, object]:
    fila = proyectar(f, SELECT_V04)
    fila["GMF"] = f.num(11)
    return {c: fila[c] for c in COLUMNAS_SABANA_V04}


def v04(spec: dict, excel: dict) -> Esperado:
    """Tipo de cuenta, y después GMF sobre las filas que pasaron la prueba de tipo de cuenta."""
    del excel  # este caso no usa homologación
    esp = Esperado()
    cuentas: dict[str, tuple[int, int]] = {}
    for p in ("CTE", "AHO"):
        sabana, tipo_no, tipo_ok, gmf_no, valida = [], [], [], [], []
        for f in detalle(spec, p):
            fila = _sabana_v04(f)
            sabana.append(fila)
            tipo_fuera = f.valor[6] not in TIPOS_CUENTA_VALIDOS
            comprobar(f, tipo_fuera, f.etiqueta == "tipo_cta_invalido", "TIPO_CTA fuera de 1 a 5")
            if tipo_fuera:
                tipo_no.append(fila)
                continue
            tipo_ok.append(fila)
            gmf = fila["GMF"]
            motivo = "GMF NO NUMERICO" if gmf is None else (
                "GMF FUERA DE RANGO" if not 1 <= gmf <= 10 else None
            )  # fmt: skip
            esperado = MOTIVO_GMF.get(f.etiqueta)
            comprobar(f, motivo is not None, esperado is not None, "GMF fuera de regla")
            if motivo is None:
                valida.append(fila)
                continue
            comprobar(f, motivo == esperado, True, f"motivo GMF {motivo} frente a {esperado}")
            gmf_no.append({**fila, "MOTIVO": motivo})
        esp.tablas[f"SABANA_{p}"] = tabla(COLUMNAS_SABANA_V04, sabana)
        esp.tablas[f"INCONS_TIPO_CTA_INVALIDO_{p}"] = tabla(COLUMNAS_TIPO_RECHAZO, tipo_no)
        esp.tablas[f"SABANA_TIPO_CTA_OK_{p}"] = tabla(COLUMNAS_TIPO_OK, tipo_ok)
        esp.tablas[f"INCONS_GMF_INVALIDO_{p}"] = tabla(COLUMNAS_GMF_RECHAZO, gmf_no)
        esp.tablas[f"SABANA_VALIDA_{p}"] = tabla(COLUMNAS_TIPO_OK, valida)
        cuenta = [
            {"RELACION": r["RELACION"], "TIPO_CTA": r["TIPO_CTA"],
             "LLAVE_NOMBRE": r["LLAVE_NOMBRE"], "GMF": r["GMF"],
             "INCONSISTENCIA": "TIPO CTA INVALIDO"} for r in tipo_no
        ] + [
            {"RELACION": r["RELACION"], "TIPO_CTA": r["TIPO_CTA"],
             "LLAVE_NOMBRE": r["LLAVE_NOMBRE"], "GMF": r["GMF"],
             "INCONSISTENCIA": r["MOTIVO"]} for r in gmf_no
        ]  # fmt: skip
        esp.tablas[f"INCONS_CUENTA_{p}"] = tabla(COLUMNAS_CUENTA, cuenta)
        esp.archivos[f"INCONS_CUENTA_{p}"] = esp.tablas[f"INCONS_CUENTA_{p}"]
        cuentas[p] = (len(cuenta), len(valida))
    esp.tablas["CONTEO_CUENTA"] = conteos(
        "PRODUCTO", "NRO_RECHAZOS", [(p, cuentas[p][0]) for p in ("CTE", "AHO")]
    )
    esp.tablas["CONTEO_CUENTA_VALIDA"] = conteos(
        "PRODUCTO", "NRO_VALIDOS", [(p, cuentas[p][1]) for p in ("CTE", "AHO")]
    )
    return esp
