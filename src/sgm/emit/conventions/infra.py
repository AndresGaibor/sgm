"""Pasos de infraestructura de un Job: conexión compartida, cierre, manejo de error y conteo.

Son recomendaciones con su motivo, no código generado. El motor de base de datos sale del componente
de acceso o, si no lo trae, de la pista del programa SAS. Si no hay motor, el paso queda como
"por_determinar" y el administrador decide el mecanismo.

Porte de la regla de `job_structure.py`; el resto de esa lógica (particiones, orquestación) se
reescribe en la pasada de particionado (hito 7).
"""

from __future__ import annotations

import re

#: Motores de base de datos que tienen componentes de Talend en el catálogo.
DATABASE_FAMILIES = (
    "DB|Mysql|Oracle|Postgresql|Mssql|Teradata|Snowflake|Redshift|Vertica|Netezza|"
    "Db2|Informix|Sybase|MariaDB|SingleStore|Greenplum|Impala|Hive"
)
#: Componentes que acceden a una base de datos (lectura, escritura, fila, procedimiento, carga masiva).
DATABASE_ACCESS = re.compile(
    rf"^t(?:{DATABASE_FAMILIES})(?:Input|Output|Row|SP|BulkExec|OutputBulk|OutputBulkExec)$"
)
DATABASE_CONNECTION = re.compile(rf"^t(?:{DATABASE_FAMILIES})Connection$")
DATABASE_CLOSE = re.compile(rf"^t(?:{DATABASE_FAMILIES})Close$")
#: Componente que detiene el Job ante un error y que cuenta como manejo de error.
ERROR_COMPONENT = "tDie"
#: Componente de conteo de registros del paso de observabilidad.
COUNT_COMPONENT = "tLogRow"
#: Máximo de componentes en un Job antes de sugerir dividirlo (regla BP-SIZE-01).
MAX_COMPONENTS_PER_JOB = 25
#: Máximo de pasos recomendados por Job; se quitan los de menor prioridad.
MAX_RECOMMENDED_PER_JOB = 4


def engine_of_access(component: str) -> str | None:
    """Motor de un componente de acceso (`tOracleInput` -> `oracle`); None si no es de base de datos."""
    match = re.match(rf"^t({DATABASE_FAMILIES})", component)
    return match.group(1).lower() if match else None


def infra_plan(engine: str | None | bool) -> list[dict[str, str]]:
    """Pasos recomendados según el motor.

    engine False: el Job no accede a bases de datos, no hay conexión ni cierre.
    engine None: hay acceso, pero el motor no se conoce; se deja por determinar.
    """
    steps: list[dict[str, str]] = []
    if engine is not False:
        if engine:
            steps.append(
                {
                    "role": "Compartida",
                    "component": f"t{engine}Connection",
                    "why": "Conexión única a la base de datos; evita abrir y cerrar sesiones por cada tabla.",
                }
            )
            steps.append(
                {
                    "role": "Cierre",
                    "component": f"t{engine}Close",
                    "why": "Cierra la conexión compartida al terminar el flujo.",
                }
            )
        else:
            steps.append(
                {
                    "role": "Compartida",
                    "component": "por_determinar",
                    "why": "Hay accesos a base de datos, pero el motor no está claro en el SAS.",
                }
            )
            steps.append(
                {
                    "role": "Cierre",
                    "component": "por_determinar",
                    "why": "Cerrar la sesión con el mecanismo que indique el administrador.",
                }
            )
    steps.append(
        {
            "role": "Error",
            "component": ERROR_COMPONENT,
            "why": "Detiene el Job ante un error de componente, igual que el ABORT o el error de SAS.",
        }
    )
    steps.append(
        {
            "role": "Conteos",
            "component": COUNT_COMPONENT,
            "why": "Muestra el conteo de registros; el SAS compara conteos y se verifica en la ejecución.",
        }
    )
    return steps
