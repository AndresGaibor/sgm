"""Pases previos a la emisión de un plan de migración."""

from pathlib import Path

from sgm.ir.models import Column, Plan
from sgm.ir.pase_copias_remotas import aplicar_copias, copias_remotas
from sgm.ir.pase_tablas_locales import tablas_locales_a_archivos
from sgm.migrar.esquemas import PendienteMigracion, esquemas_de_entrada
from sgm.migrar.esquemas_paso_directo import esquemas_paso_directo
from sgm.migrar.tablas_locales import TablaLocal


def preparar_plan(
    plan: Plan, locales: dict[str, TablaLocal] | None = None, texto: str = ""
) -> tuple[Plan, list[PendienteMigracion]]:
    """Convierte fuentes locales y resuelve alias de copias remotas declaradas en el SAS."""
    plan, pendientes = tablas_locales_a_archivos(plan, locales or {})
    copias, pendientes_copia = copias_remotas(texto)
    plan, sin_efecto = aplicar_copias(plan, copias)
    return plan, [*pendientes, *pendientes_copia, *sin_efecto]


def esquemas_con_locales(
    plan: Plan,
    catalogo: dict[str, list[Column]],
    muestra: Path | None,
    locales: dict[str, TablaLocal],
):
    """Prioriza columnas de ficha solo para lecturas realmente convertidas."""
    aplicadas = {
        str(op.params["_tabla_local"])
        for op in plan.graph.operators()
        if op.kind == "read_file" and op.params.get("_tabla_local")
    }
    catalogo = dict(catalogo)
    catalogo.update({nombre: list(locales[nombre].columnas) for nombre in aplicadas})
    tablas, pendientes = esquemas_de_entrada(plan, catalogo, muestra)
    tablas.update(esquemas_paso_directo(plan, catalogo, muestra))
    tablas.update({nombre: list(locales[nombre].columnas) for nombre in aplicadas})
    return tablas, pendientes
