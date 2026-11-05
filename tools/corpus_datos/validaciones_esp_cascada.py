"""Esperado por construcción de las cadenas secuenciales: v07 (CTE y AHO) y v08 (Nequi).

Cada etapa del programa toma solo las filas que la etapa anterior dejó pasar. Una fila rechazada
en `PASO1` no llega a `PASO2`, y así sucesivamente. La decisión sale de la etiqueta de defecto; la
condición del programa se aplica al contenido solo para comprobar la coherencia (`comprobar`).

En v07 el programa convierte GMF igual que NRO_DOC (`GMF = input(left(GMF_TXT), 3.)`, con
`GMF_TXT` borrada), así que la sabana trae GMF al final, como en v04 a v06 y v08.
"""

from __future__ import annotations

from validaciones_esp_documento import COLUMNAS_DOC  # noqa: E402
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

# SELECT de v07 y v08: NRO_DOC y GMF son texto en el SELECT y se convierten después.
SELECT_CASCADA = [
    (1, "ANIO_PROCESO"), (2, "MES_PROCESO"), (4, "RELACION"), (6, "TIPO_CTA"), (7, "NRO_CTA"),
    (8, "LLAVE_NOMBRE"), (9, "TIPO_DOC"), (10, "NRO_DOC_TXT"), (11, "GMF_TXT"),
    (23, "FIN_SALDO_CTA"),
]  # fmt: skip
# Sabana de cascada: las conversiones agregan NRO_DOC y luego GMF al final.
COLUMNAS_SABANA = [
    "ANIO_PROCESO", "MES_PROCESO", "RELACION", "TIPO_CTA", "NRO_CTA", "LLAVE_NOMBRE", "TIPO_DOC",
    "FIN_SALDO_CTA", "NRO_DOC", "GMF",
]  # fmt: skip
COLUMNAS_CUENTA = [*COLUMNAS_DOC, "GMF", "FIN_SALDO_CTA"]
COLUMNAS_RECHAZOS = ["RELACION", "TIPO_CTA", "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "MOTIVO"]
TIPOS_CUENTA_VALIDOS = {1, 2, 3, 4, 5}


def _sabana(f: Fila) -> dict[str, object]:
    """Fila de la sabana tras las conversiones de NRO_DOC y GMF del caso."""
    fila = proyectar(f, SELECT_CASCADA)
    fila["NRO_DOC"] = f.num(10)
    fila["GMF"] = f.num(11)
    return {c: fila[c] for c in COLUMNAS_SABANA}


def _sin_documento(f: Fila) -> bool:
    numero = f.num(10)
    return numero is None or numero == 0


def _distinct(filas: list[dict]) -> list[dict]:
    """`SELECT DISTINCT`: quita duplicados exactos y conserva el primero."""
    vistas: set[tuple] = set()
    salida: list[dict] = []
    for fila in filas:
        clave = tuple(fila.values())
        if clave not in vistas:
            vistas.add(clave)
            salida.append(fila)
    return salida


def _coherencia(f: Fila, excel: dict) -> None:
    """Comprueba que las etiquetas dicen lo mismo que el contenido, para las tres reglas."""
    homol = excel_codigos(excel, "homol_tipo_doc")
    comprobar(f, f.valor[9] not in homol, f.etiqueta == "tipo_doc_invalido", "TIPO_DOC")
    if f.etiqueta != "tipo_doc_invalido":
        es_doc = f.etiqueta.startswith(("tit_cot", "fa_"))
        comprobar(f, _sin_documento(f), es_doc, "NRO_DOC vacío o cero")
    comprobar(
        f, f.valor[6] not in TIPOS_CUENTA_VALIDOS, f.etiqueta == "tipo_cta_invalido",
        "TIPO_CTA fuera de 1 a 5",
    )  # fmt: skip


def v07(spec: dict, excel: dict) -> Esperado:
    """Cadena completa: tipo de documento, documento vacío o cero, y tipo de cuenta."""
    esp = Esperado()
    rechazos_totales: dict[str, list[dict]] = {}
    for p in ("CTE", "AHO"):
        filas = detalle(spec, p)
        sab = [_sabana(f) for f in filas]
        por_etapa: dict[str, list[dict]] = {k: [] for k in (
            "P1R", "P1V", "P2TC", "P2FA", "P2V", "P3R", "FINAL")}  # fmt: skip
        for f, fila in zip(filas, sab, strict=True):
            _coherencia(f, excel)
            e = f.etiqueta
            if e == "tipo_doc_invalido":
                por_etapa["P1R"].append(fila)
                continue
            por_etapa["P1V"].append(fila)
            if e.startswith("tit_cot"):
                por_etapa["P2TC"].append(fila)
                continue
            if e.startswith("fa_"):
                por_etapa["P2FA"].append(fila)
                continue
            por_etapa["P2V"].append(fila)
            if e == "tipo_cta_invalido":
                por_etapa["P3R"].append(fila)
            else:
                por_etapa["FINAL"].append(fila)
        _tablas_cascada(esp, p, sab, por_etapa)
        rechazos_totales[p] = _rechazos(por_etapa)
        esp.tablas[f"RECHAZOS_{p}"] = tabla(COLUMNAS_RECHAZOS, rechazos_totales[p])
        esp.archivos[f"RECHAZOS_{p}"] = esp.tablas[f"RECHAZOS_{p}"]
        esp.archivos[f"SABANA_FINAL_{p}"] = esp.tablas[f"SABANA_FINAL_{p}"]
    return esp


def _tablas_cascada(
    esp: Esperado, p: str, sabana: list[dict], etapa: dict[str, list[dict]]
) -> None:
    esp.tablas[f"SABANA_{p}"] = tabla(COLUMNAS_SABANA, sabana)
    esp.tablas[f"PASO1_RECHAZO_{p}"] = tabla(COLUMNAS_CUENTA, etapa["P1R"])
    esp.tablas[f"PASO1_VALIDO_{p}"] = tabla(COLUMNAS_SABANA, etapa["P1V"])
    esp.tablas[f"PASO2_RECHAZO_TC_{p}"] = tabla(COLUMNAS_SABANA, etapa["P2TC"])
    esp.tablas[f"PASO2_RECHAZO_FA_{p}"] = tabla(COLUMNAS_SABANA, etapa["P2FA"])
    esp.tablas[f"PASO2_VALIDO_{p}"] = tabla(COLUMNAS_SABANA, etapa["P2V"])
    esp.tablas[f"PASO3_RECHAZO_{p}"] = tabla(COLUMNAS_SABANA, etapa["P3R"])
    esp.tablas[f"SABANA_FINAL_{p}"] = tabla(COLUMNAS_SABANA, etapa["FINAL"])


def _rechazos(etapa: dict[str, list[dict]]) -> list[dict]:
    """`OUTER UNION CORR` de los rechazos, en el orden de las etapas del programa."""
    motivos = [
        (etapa["P1R"], "TIPO DOC INVALIDO"),
        (etapa["P2TC"], "NRO DOC VACIO O CERO"),
        (etapa["P2FA"], "NRO DOC FA VACIO O CERO"),
        (etapa["P3R"], "TIPO CTA INVALIDO"),
    ]
    filas: list[dict] = []
    for grupo, motivo in motivos:
        filas.extend({**{c: r[c] for c in COLUMNAS_RECHAZOS[:-1]}, "MOTIVO": motivo} for r in grupo)
    return filas


def v08(spec: dict, excel: dict) -> Esperado:
    """Cadena de Nequi: tipo de documento y documento vacío o cero, sin tipo de cuenta."""
    esp = Esperado()
    homol = excel_codigos(excel, "homol_nequi")
    filas = detalle(spec, "NEQUI")
    sab = [_sabana(f) for f in filas]
    tipo_inv, tit, fa, valido, sin_vacios = [], [], [], [], []
    for f, fila in zip(filas, sab, strict=True):
        comprobar(f, f.valor[9] not in homol, f.etiqueta == "tipo_doc_invalido", "TIPO_DOC")
        if f.etiqueta == "tipo_doc_invalido":
            tipo_inv.append(fila)
            continue
        valido.append(fila)
        if f.etiqueta.startswith("tit_cot"):
            comprobar(f, _sin_documento(f), True, "NRO_DOC tit-cot")
            tit.append(fila)
            continue
        if f.etiqueta.startswith("fa_"):
            comprobar(f, _sin_documento(f), True, "NRO_DOC FA")
            fa.append(fila)
            continue
        comprobar(f, _sin_documento(f), False, "NRO_DOC válido")
        sin_vacios.append(fila)
    final = _distinct([{c: r[c] for c in COLUMNAS_CUENTA} for r in sin_vacios])
    rechazos = _rechazos({
        "P1R": tipo_inv, "P2TC": tit, "P2FA": fa, "P3R": [],
    })  # fmt: skip
    esp.tablas["SABANA_NEQUI"] = tabla(COLUMNAS_SABANA, sab)
    esp.tablas["TIPO_DOC_INVALIDO_NEQUI"] = tabla(COLUMNAS_DOC, tipo_inv)
    esp.tablas["TIPO_DOC_VALIDO_NEQUI"] = tabla(COLUMNAS_SABANA, valido)
    esp.tablas["NRO_DOC_VACIO_0_TIT_COT_NEQUI"] = tabla(COLUMNAS_SABANA, tit)
    esp.tablas["INCONS_NRO_DOC_FA_NEQUI"] = tabla(COLUMNAS_SABANA, fa)
    esp.tablas["SABANA_SIN_VACIOS_NEQUI"] = tabla(COLUMNAS_SABANA, sin_vacios)
    esp.tablas["SABANA_FINAL_NEQUI"] = tabla(COLUMNAS_CUENTA, final)
    esp.tablas["RECHAZOS_NEQUI"] = tabla(COLUMNAS_RECHAZOS, rechazos)
    suma = sum(r["FIN_SALDO_CTA"] for r in final)
    esp.tablas["SUMA_SALDO_NEQUI_FINAL"] = tabla(
        ["SUMA_SALDO_FINAL_NEQUI"], [{"SUMA_SALDO_FINAL_NEQUI": suma}]
    )
    esp.tablas["CONTEO_NEQUI"] = conteos(
        "ESTADO", "NRO_FILAS", [("VALIDO", len(final)), ("RECHAZO", len(rechazos))]
    )
    esp.archivos["SABANA_FINAL_NEQUI"] = esp.tablas["SABANA_FINAL_NEQUI"]
    esp.archivos["RECHAZOS_NEQUI"] = esp.tablas["RECHAZOS_NEQUI"]
    return esp
