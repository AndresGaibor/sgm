"""Sustituye lecturas de bibliotecas locales por sus archivos declarados."""

from sgm.ir.models import Plan
from sgm.migrar.esquemas import PendienteMigracion
from sgm.migrar.tablas_locales import TablaLocal


def tablas_locales_a_archivos(
    plan: Plan, locales: dict[str, TablaLocal]
) -> tuple[Plan, list[PendienteMigracion]]:
    """Transforma únicamente lecturas locales declaradas y avisa sobre datos sintéticos."""
    pendientes = []
    avisadas = set()
    convertidas = []
    for op in plan.graph.operators():
        if op.kind != "read" or plan.graph.predecessors(op.id):
            continue
        nombre = str(op.params.get("dataset") or "")
        tabla = locales.get(nombre.lower())
        if not tabla:
            continue
        op.kind = "read_file"
        op.component = {"name": "tFileInputDelimited"}
        convertidas.append(op.id)
        op.params = {
            "datafile": tabla.archivo,
            "outputs": [nombre],
            "dbms": "csv",
            "delimiter": tabla.delimitador,
            "getnames": True,
            "sheet": None,
            "guessingrows": None,
            "input_names": [c.name for c in tabla.columnas],
            "_tabla_local": tabla.nombre,
        }
        if tabla.origen == "sintetico" and tabla.nombre not in avisadas:
            linea = op.evidence[0].line_start if op.evidence else None
            pendientes.append(
                PendienteMigracion(
                    "P-DATOS-SINTETICOS",
                    f"tabla local {tabla.nombre} leída del fixture {tabla.archivo}, "
                    "datos sintéticos; no son datos reales",
                    linea,
                )
            )
            avisadas.add(tabla.nombre)
    for fuente in convertidas:
        dependientes = plan.graph.descendants(fuente)
        for job in plan.jobs:
            ubicacion = next(
                (
                    i
                    for i, sub in enumerate(job.subjobs)
                    if fuente in sub or any(op in dependientes for op in sub)
                ),
                None,
            )
            if ubicacion is None:
                continue
            for sub in job.subjobs:
                if fuente in sub:
                    sub.remove(fuente)
            job.subjobs[ubicacion].insert(0, fuente)
    return plan, pendientes
