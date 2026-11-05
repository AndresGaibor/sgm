"""Filas ficticias de los casos L8 de validaciones: una anomalía por fila, sin cabecera.

Cada fila de producto tiene 23 campos separados por `;`, en el orden que el original demuestra
(`VAR1`..`VAR23`). Los códigos (tipo de documento, tipo de cuenta, GMF, país, DANE) son inventados:
los valores permitidos del corpus son reglas de ejemplo, no las del cliente. Ver `caso.yaml`.
"""

from __future__ import annotations

from dataclasses import dataclass

FA = "9902"  # relación de la fila de fianza (FA) en las reglas de ejemplo
TIT_COT = "1001"  # relación titular-cotitular en las reglas de ejemplo
CODEX = "1000"  # relación que dispara la regla de Codex en el caso v05

# Nombres por posición de los 23 campos (lo confirma `origenes_producto` en la prueba unitaria).
NOMBRES_23 = (
    "ANIO_PROCESO", "MES_PROCESO", "VAR3", "RELACION", "VAR5", "TIPO_CTA", "NRO_CTA",
    "LLAVE_NOMBRE", "TIPO_DOC", "NRO_DOC", "GMF", "VAL_CRED_MES", "NRO_CRED_MES",
    "PROM_CRED_MES", "MED_CRED_MES", "VAL_DEB_MES", "NRO_DEB_MES", "PROM_DEB_MES",
    "MED_SALDO_CTA", "PROM_SALDO_CTA", "MAX_SALDO_CTA", "MIN_SALDO_CTA", "FIN_SALDO_CTA",
)  # fmt: skip


@dataclass(frozen=True)
class Producto:
    """Producto del corpus: su archivo de 23 columnas y sus códigos de tipo de documento."""

    nombre: str
    archivo: str
    tipos_doc: tuple[str, ...]  # códigos válidos en su homologación
    tipo_invalido: str  # código que no homologa para este producto


PRODUCTOS = {
    "CTE": Producto("CTE", "DETALLE_CTE.csv", ("TD01", "TD02", "TD03", "TD04"), "TD99"),
    "AHO": Producto("AHO", "DETALLE_AHO.csv", ("TD01", "TD02", "TD03", "TD04"), "TD99"),
    # En la homologación de Nequi no está TD04: es válido en general e inválido aquí.
    "NEQUI": Producto("NEQUI", "DETALLE_NEQUI.csv", ("TD01", "TD02", "TD03", "TD05"), "TD04"),
}


def secuencia(conteos: dict[str, int]) -> list[str]:
    """Una etiqueta de defecto por fila, en el orden del diccionario (los válidos al final)."""
    return [defecto for defecto, n in conteos.items() for _ in range(n)]


def _campos_base(i: int, producto: Producto) -> list[str]:
    """Fila válida: fianza cada cinco filas, tipo de cuenta 1 a 5, GMF 1 a 9, saldos positivos."""
    n = i + 1
    relacion = FA if i % 5 == 0 else TIT_COT
    primeros = [
        "2026", "10", "FIC", relacion, "S", str(1 + i % 5), f"5{n:09d}", f"LLV{n:05d}",
        producto.tipos_doc[i % len(producto.tipos_doc)], f"{n:08d}", str(1 + i % 9),
    ]  # fmt: skip
    return primeros + [f"{1000 * k + n}" for k in range(1, 13)]


def _relacion_de(defecto: str) -> str:
    """Los defectos de documento se nombran `fa_` o `tit_cot_` según la relación que afectan."""
    return FA if defecto.startswith("fa_") else TIT_COT


def fila_detalle(defecto: str, i: int, producto: Producto) -> list[str]:
    """Fila de 23 campos con a lo sumo un defecto (el de `defecto`)."""
    n = i + 1
    campos = _campos_base(i, producto)
    if defecto == "validos":
        return campos
    if defecto == "tipo_doc_invalido":
        campos[8] = producto.tipo_invalido
    elif defecto.endswith("nro_doc_vacio"):
        campos[3], campos[9] = _relacion_de(defecto), ""
    elif defecto.endswith("nro_doc_cero"):
        campos[3], campos[9] = _relacion_de(defecto), "0"
    elif defecto in ("tipo_cta_invalido", "tipo_cta_invalido_no_validado"):
        campos[5] = "9"
    elif defecto == "gmf_invalido":
        campos[10] = "XX"  # no es número: el informat 3. deja faltante
    elif defecto == "gmf_fuera_rango":
        campos[10] = "99"
    elif defecto == "codex_invalido":
        campos[3], campos[10] = CODEX, "11"
    elif defecto == "saldo_negativo":
        campos[22] = "-" + campos[22]
    elif defecto == "nombre_minusculas":
        campos[7] = f"cliente ficticio {n:05d}"
    elif defecto == "nombre_con_enie":
        campos[7] = f"NIÑO FICTICIO {n:05d}"
    elif defecto == "nombre_con_tildes":
        campos[7] = f"MARÍA FICTICIA {n:05d}"
    elif defecto == "nombre_con_espacios":
        campos[7] = f"  CLIENTE   FICTICIO {n:05d} "
    elif defecto == "valor_con_espacios":
        campos[11] = " 1200 "
    else:
        raise ValueError(f"defecto de detalle desconocido: {defecto}")
    return campos


def fila_ubicacion(defecto: str, i: int) -> list[str]:
    """Fila auxiliar de ubicación: llave, país, código DANE y dirección (cuatro campos)."""
    llave = f"LLV{i + 1:05d}"
    if defecto == "pais_no_homologado":
        return [llave, "777", "", "CALLE FICTICIA 10 20 30"]
    if defecto == "dane_no_homologado":
        return [llave, "900", "99999", "CALLE FICTICIA 10 20 30"]
    if defecto == "ubicacion_extranjera_con_codigo":
        return [llave, "902", "99001", "AVENIDA FICTICIA 5 6 7"]
    if defecto == "direccion_invalida":
        return [llave, "900", "99002", "SIN DIR"]
    if defecto == "validos":
        if i % 2:
            return [llave, "903", "", "CARRERA FICTICIA 1 2 3"]
        return [llave, "900", f"9900{1 + i % 3}", "CALLE FICTICIA 8 9 10"]
    raise ValueError(f"defecto de ubicación desconocido: {defecto}")
