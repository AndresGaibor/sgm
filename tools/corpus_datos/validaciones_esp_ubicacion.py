"""Esperado por construcción de v03: país y código DANE contra los Excel de homologación.

La sabana recorre el detalle (`t1`) y se une por llave a la ubicación (`t2`, LEFT JOIN). La decisión
de rechazo sale de la etiqueta de la fila de ubicación; el `CASE` del programa se aplica al
contenido para comprobar que el motivo que da el programa es el que dice la etiqueta.
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
    ubicacion,
)

PAIS_NACION = "900"  # el programa exige código DANE solo para este país
SELECT_V03 = [
    (1, "ANIO_PROCESO"), (2, "MES_PROCESO"), (4, "RELACION"), (6, "TIPO_CTA"), (7, "NRO_CTA"),
    (8, "LLAVE_NOMBRE"), (9, "TIPO_DOC"), (10, "NRO_DOC"),
]  # fmt: skip
COLUMNAS_SABANA = [a for _, a in SELECT_V03]
COLUMNAS_SABANA_UBIC = [
    "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "PAIS",
    "CODIGO_UBICACION", "DIRECCION",
]  # fmt: skip
COLUMNAS_UBIC = ["LLAVE_NOMBRE", "PAIS", "CODIGO_UBICACION", "DIRECCION"]
COLUMNAS_INCONS = [
    "LLAVE_NOMBRE", "RELACION", "TIPO_DOC", "NRO_DOC", "PAIS", "CODIGO_UBICACION", "DIRECCION",
    "INCONSISTENCIA",
]  # fmt: skip
COLUMNAS_UBIC_VALIDA = [
    "LLAVE_NOMBRE", "RELACION", "TIPO_DOC", "NRO_DOC", "PAIS", "CODIGO_UBICACION", "DIRECCION",
]  # fmt: skip
MOTIVO_POR_ETIQUETA = {
    "pais_no_homologado": "PAIS NO HOMOLOGADO",
    "dane_no_homologado": "DANE NO HOMOLOGADO",
    "ubicacion_extranjera_con_codigo": "UBICACION EXTRANJERA CON CODIGO",
    "direccion_invalida": "DIRECCION INVALIDA",
}


def _motivo_caso(u: Fila, pais_ok: set[str], dane_ok: set[str]) -> str | None:
    """`CASE` y `WHERE` del programa sobre el contenido de la ubicación; None si es válida."""
    pais = str(u.valor[2])
    codigo = u.valor[3]
    direccion = u.valor[4]
    if pais not in pais_ok:
        return "PAIS NO HOMOLOGADO"
    if pais == PAIS_NACION and str(codigo) not in dane_ok:
        return "DANE NO HOMOLOGADO"
    if pais != PAIS_NACION and codigo is not None:
        return "UBICACION EXTRANJERA CON CODIGO"
    if len(direccion) < 8 or "SIN DIR" in direccion.upper():
        return "DIRECCION INVALIDA"
    return None


def v03(spec: dict, excel: dict) -> Esperado:
    """País y código DANE contra los dos Excel; el primer motivo que aplique gana (`CASE`)."""
    esp = Esperado()
    pais_ok = excel_codigos(excel, "pais", 0)
    dane_ok = excel_codigos(excel, "dane", 0)
    esp.tablas["FORMATO_CODIGO_DANE"] = tabla(
        ["CODIGO_DANE"], [{"CODIGO_DANE": fila[0]} for fila in excel["dane"][2]]
    )
    rechazos: dict[str, int] = {}
    validos: dict[str, int] = {}
    for p in ("CTE", "AHO"):
        ubic = ubicacion(spec, p)
        por_llave = {u.valor[1]: u for u in ubic}
        sabana, sabana_ubic, incons, valida = [], [], [], []
        for f in detalle(spec, p):
            fila = proyectar(f, SELECT_V03)
            sabana.append(fila)
            u = por_llave[f.valor[8]]
            ubic_fila = {
                "RELACION": fila["RELACION"], "TIPO_CTA": fila["TIPO_CTA"],
                "NRO_CTA": fila["NRO_CTA"], "LLAVE_NOMBRE": fila["LLAVE_NOMBRE"],
                "TIPO_DOC": fila["TIPO_DOC"], "NRO_DOC": fila["NRO_DOC"],
                "PAIS": u.valor[2], "CODIGO_UBICACION": u.valor[3],
                "DIRECCION": u.valor[4],
            }  # fmt: skip
            sabana_ubic.append(ubic_fila)
            motivo = _motivo_caso(u, pais_ok, dane_ok)
            esperado = MOTIVO_POR_ETIQUETA.get(u.etiqueta)
            comprobar(u, motivo is not None, esperado is not None, "ubicación rechazada")
            if motivo is None:
                valida.append(ubic_fila)
                continue
            comprobar(u, motivo == esperado, True, f"motivo {motivo} frente a {esperado}")
            incons.append({**ubic_fila, "INCONSISTENCIA": motivo})
        esp.tablas[f"SABANA_{p}"] = tabla(COLUMNAS_SABANA, sabana)
        esp.tablas[f"UBIC_{p}"] = tabla(
            COLUMNAS_UBIC,
            [{"LLAVE_NOMBRE": u.valor[1], "PAIS": u.valor[2], "CODIGO_UBICACION": u.valor[3],
              "DIRECCION": u.valor[4]} for u in ubic],  # fmt: skip
        )
        esp.tablas[f"SABANA_UBIC_{p}"] = tabla(COLUMNAS_SABANA_UBIC, sabana_ubic)
        esp.tablas[f"INCONS_UBICACION_{p}"] = tabla(COLUMNAS_INCONS, incons)
        esp.tablas[f"UBIC_VALIDA_{p}"] = tabla(COLUMNAS_UBIC_VALIDA, valida)
        esp.archivos[f"INCONS_UBICACION_{p}"] = esp.tablas[f"INCONS_UBICACION_{p}"]
        rechazos[p], validos[p] = len(incons), len(valida)
    esp.tablas["CONTEO_UBICACION"] = conteos(
        "PRODUCTO", "NRO_RECHAZOS", [(p, rechazos[p]) for p in ("CTE", "AHO")]
    )
    esp.tablas["CONTEO_UBICACION_VALIDA"] = conteos(
        "PRODUCTO", "NRO_VALIDOS", [(p, validos[p]) for p in ("CTE", "AHO")]
    )
    return esp
