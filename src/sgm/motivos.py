"""Registro de motivos de hueco (F1.1): cada motivo tiene dueño y se sabe si está en el contrato.

Los motivos de la lista del contrato (`docs/plan-sgm-v2/05-contratos.md`, sección 3) son los que
el equipo acordó. Los que el código usa y no están en esa lista se marcan `contrato=False` hasta que
los tres los acepten: cambiar la lista es un cambio de contrato.

Los motivos `no_hueco` no son huecos: son estados que el código registra en `not_migrated`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Motivo:
    codigo: str
    dueño: str  # joseph, byron o andres (ver docs/plan-sgm-v2/01-reparto.md)
    contrato: bool  # está en la lista cerrada del contrato
    se_cierra_con: str


HUECOS: tuple[Motivo, ...] = (
    Motivo("PARSE_ERROR", "joseph", True, "corrección del parser y caso de prueba"),
    Motivo("SENTENCIA_NO_SOPORTADA", "joseph", True, "rules/sas/statements/*.yaml"),
    Motivo("PROC_NO_SOPORTADO", "joseph", True, "rules/sas/procs/*.yaml"),
    Motivo("MACRO_DINAMICA", "joseph", True, "mejora del expansor o decisión del usuario"),
    Motivo("INCLUDE_EXTERNO", "byron", True, "env/externals/ o env/externals.json"),
    Motivo("FUNCION_NO_MAPEADA", "joseph", True, "rules/sas/functions/*.yaml"),
    Motivo("TIPO_DESCONOCIDO", "byron", True, "env/schemas/ o rules/sas/informats.yaml"),
    Motivo("COMPONENTE_NO_CATALOGADO", "byron", True, "rules/mapping/*.yaml o catálogo"),
    Motivo("SEMANTICA_DUDOSA", "andres", True, "alternativas en la regla y decisión del usuario"),
    Motivo("INTRINSECO_PARCIAL", "joseph", True, "rules/sas/intrinsics/*.yaml o pasada 3"),
    Motivo(
        "COMANDO_SISTEMA", "joseph", False, "regla de sentencia de sistema (pendiente de contrato)"
    ),
    Motivo("MACRO_NO_EXPANDIDA", "joseph", False, "mejora del expansor (pendiente de contrato)"),
    Motivo("SQL_NO_SOPORTADO", "joseph", False, "regla de sentencia SQL (pendiente de contrato)"),
)

NO_HUECO: tuple[str, ...] = (
    "CONFIGURACION",  # sesión o macro: lo resuelve el contexto del Job
    "CONEXION_SQL",  # conexión a un motor: fontanería
    "INCLUDE_DECLARADO",  # %include declarado: contexto y no migrado
    "REPORTE",  # reporte impreso: lo decide la política `reports`
)

_POR_CODIGO = {m.codigo: m for m in HUECOS}


def de(codigo: str) -> Motivo | None:
    """Motivo registrado, o None si el código no está en el registro."""
    return _POR_CODIGO.get(codigo)


def sin_registrar(codigos: set[str]) -> set[str]:
    """Motivos usados que no están en el registro de huecos ni en la lista de no-huecos."""
    return {c for c in codigos if c not in _POR_CODIGO and c not in NO_HUECO}
