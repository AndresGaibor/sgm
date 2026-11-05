"""R1-06 (parte 2): la forma del **SAS real** de cuenta/GMF, leída del `client_large.sas`.

El hito 88 tradujo el caso pequeño `v04` (`TIPO_CTA NOT IN ('1'..'5')`, `GMF IS MISSING OR
NOT BETWEEN`, dos motivos para GMF y un `CASE`). El programa real escribe la misma idea de otra
forma y **no se unifican**::

    INCONS_TIPO_CTA_INVALIDO_<P>:  TIPO_CTA NOT BETWEEN 1 AND 5  AND RELACION = 1000
    INCONS_CODEX_INVALIDO_<P>:     GMF      NOT BETWEEN 1 AND 10 AND RELACION = 1000

Ambas salen de `proceso.reglas.reglas` (hito 74), que ya lee el rango, el control y el motivo del
paso `DATA` (`TIPO CTA INVALIDO` / `CODEX INVALIDO`). El orden importa: el codex se evalúa sobre
`SABANA_TIPO_CTA_VALIDO_<P>`, es decir, solo en las filas que ya pasaron la primera regla. Las
filas con `RELACION <> 1000` quedan exentas de las dos comprobaciones, tal como confirma el
`WHERE` final `FINAL_VALIDAR_CTA_Y_GMF_*`.

Este módulo no inventa columnas, motivos ni nombres de tabla: exige que las dos reglas existan por
producto con la misma forma, que las proyecciones de los `CREATE TABLE` coincidan y que las tablas
`INCONS_PAQ_*` (las que llegan al `OUTER UNION CORR`) proyecten exactamente esas columnas más
`INCONSISTENCIA`. Lo que queda fuera se devuelve como pendiente, nunca se descarta en silencio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.reglas import ReglaRango, reglas

# Prefijos de las dos tablas de rechazo, tal como las nombra el programa real.
PREFIJOS = {
    "tipo_cta": "INCONS_TIPO_CTA_INVALIDO_",
    "codex": "INCONS_CODEX_INVALIDO_",
}
# Bases de los CSV que escribe el Job: las tres primeras son tablas del SAS; `cuenta` es la
# consolidación derivada de los `INCONS_PAQ_*` + `OUTER UNION CORR` (no existe como tabla única).
TABLAS = {
    "tipo_cta": "INCONS_TIPO_CTA_INVALIDO",
    "codex": "INCONS_CODEX_INVALIDO",
    "valido": "SABANA_CODEX_VALIDO",
    "cuenta": "INCONS_CUENTA",
}
MODOS = ("tipo_cta", "codex", "valido", "cuenta")
INCONSISTENCIA = "INCONSISTENCIA"

_CREAR = re.compile(
    r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<tabla>\w+)\s+AS\s+SELECT\s+"
    r"(?P<cuerpo>.*?)\s+FROM\b"
)
_CAMPO = re.compile(r"(?i)^\s*\w+\.(\w+)\s*$")


@dataclass(frozen=True)
class ReglasCuentaReal:
    """Lo que el SAS real demuestra para separar cuenta y codex, ya canónico por producto."""

    tipo_cta: ReglaRango
    codex: ReglaRango
    columnas: tuple[str, ...]
    tablas: dict[str, str]

    @property
    def control(self) -> tuple[str, str]:
        """`RELACION = 1000`, leído del `WHERE` y compartido por las dos reglas."""
        assert self.tipo_cta.control is not None
        return self.tipo_cta.control

    @property
    def motivos(self) -> dict[str, str]:
        return {"tipo_cta": self.tipo_cta.motivo, "codex": self.codex.motivo}


def proyeccion(texto: str, tabla: str) -> tuple[str, ...]:
    """Columnas del `SELECT` de un `CREATE TABLE` concreto; falla si no se leen enteras.

    Se lee una tabla por vez a propósito: el programa tiene `SELECT *` en los `OUTER UNION CORR`,
    y un lector global que intentara interpretarlos no podría devolver una proyección honesta.
    """
    for crear in _CREAR.finditer(texto):
        if crear.group("tabla").upper() != tabla.upper():
            continue
        columnas: list[str] = []
        for parte in crear.group("cuerpo").split(","):
            campo = _CAMPO.fullmatch(parte.strip())
            if campo is None:
                raise ValueError(
                    f"{tabla}: no se puede leer la columna {parte.strip()!r} del SELECT"
                )
            columnas.append(campo.group(1).upper())
        return tuple(columnas)
    raise ValueError(f"El SAS no declara `CREATE TABLE {tabla} AS SELECT ... FROM`")


def _forma(regla: ReglaRango) -> tuple:
    """Lo que define a la regla, sin el destino ni la línea: todos los productos deben coincidir."""
    return (regla.columna, regla.desde, regla.hasta, regla.permite, regla.motivo, regla.control)


def _productos(grupo: list[ReglaRango], prefijo: str) -> tuple[str, ...]:
    return tuple(sorted({r.destino[len(prefijo) :] for r in grupo}))


def _revisar_columnas(texto: str, productos: tuple[str, ...]) -> tuple[str, ...]:
    """Las 19 columnas de los rechazos y las 20 de las tablas con `INCONSISTENCIA`."""
    bases: dict[str, tuple[str, ...]] = {}
    nombres = {
        "tipo_cta": "INCONS_TIPO_CTA_INVALIDO_{p}",
        "codex": "INCONS_CODEX_INVALIDO_{p}",
        "valido": "SABANA_CODEX_VALIDO_{p}",
        "paq_tipo_cta": "INCONS_PAQ_TIPO_CTA_INV_{p}",
        "paq_codex": "INCONS_PAQ_GMF_INV_{p}",
    }
    for clave, plantilla in nombres.items():
        for producto in productos:
            columnas = proyeccion(texto, plantilla.format(p=producto))
            anterior = bases.setdefault(clave, columnas)
            if anterior != columnas:
                raise ValueError(
                    f"{clave}: los productos proyectan columnas distintas: {anterior}, {columnas}"
                )
    rechazo = bases["tipo_cta"]
    if not rechazo:
        raise ValueError("El SAS no proyecta columnas en las tablas de rechazo de cuenta")
    if any(bases[c] != rechazo for c in ("codex", "valido")):
        raise ValueError("Los tres flujos de cuenta no proyectan las mismas columnas")
    con_motivo = (*rechazo, INCONSISTENCIA)
    if any(bases[c] != con_motivo for c in ("paq_tipo_cta", "paq_codex")):
        raise ValueError("Las tablas INCONS_PAQ_* no proyectan las 19 columnas + INCONSISTENCIA")
    return rechazo


def reglas_cuenta_real(texto: str) -> tuple[ReglasCuentaReal, list[str]]:
    """Las dos reglas canónicas del SAS real y las reglas que quedan fuera del Job emitido.

    Un programa que no declara la pareja completa, el control, los motivos o las proyecciones no
    produce reglas a medias: se rechaza con `ValueError` y `cli_talend` lo publica como pendiente.
    """
    todas = reglas(texto)
    grupos = {
        modo: [r for r in todas if r.destino.upper().startswith(prefijo)]
        for modo, prefijo in PREFIJOS.items()
    }
    for modo, grupo in grupos.items():
        if not grupo:
            raise ValueError(f"El SAS no declara la regla '{modo}' de cuenta/GMF")
        if len({_forma(r) for r in grupo}) != 1:
            raise ValueError(f"Los productos declaran reglas '{modo}' distintas: {grupo}")
        muestra = grupo[0]
        if muestra.permite or muestra.control is None or not muestra.motivo:
            raise ValueError(
                f"La regla '{modo}' debe ser `NOT BETWEEN` con control y motivo del SAS: {muestra}"
            )
    if grupos["tipo_cta"][0].control != grupos["codex"][0].control:
        raise ValueError("Las dos reglas de cuenta no comparten el control de RELACION")
    productos = _productos(grupos["tipo_cta"], PREFIJOS["tipo_cta"])
    if productos != _productos(grupos["codex"], PREFIJOS["codex"]):
        raise ValueError("Los productos de las dos reglas de cuenta no coinciden")
    columnas = _revisar_columnas(texto, productos)
    seleccionadas = {id(r) for grupo in grupos.values() for r in grupo}
    otras = [r for r in todas if id(r) not in seleccionadas]
    pendientes = [
        f"R1-06: {len(otras)} reglas de rango del SAS siguen sin emitir "
        "(NEQUI, DOC_INCORRECTOS_*, FINAL_VALIDAR_*)",
        "R1-06: el INNER JOIN de INCONS_PAQ_* y el OUTER UNION CORR de INCONS_DEP_* se "
        "consolidan en una salida derivada INCONS_CUENTA_*",
        "R1-07: los saldos negativos no se separan en este Job; SABANA_CODEX_VALIDO_* no es "
        "SABANA_VALIDA_*",
    ]
    return (
        ReglasCuentaReal(
            tipo_cta=grupos["tipo_cta"][0],
            codex=grupos["codex"][0],
            columnas=columnas,
            tablas=dict(TABLAS),
        ),
        pendientes,
    )


__all__ = [
    "INCONSISTENCIA",
    "MODOS",
    "PREFIJOS",
    "ReglasCuentaReal",
    "TABLAS",
    "proyeccion",
    "reglas_cuenta_real",
]
