"""Informes de `sgm migrar`: los cuatro documentos que la persona lee después de la corrida.

El Job se abre en Studio, pero las decisiones y los huecos no están en el `.item`: están aquí. Por
eso los informes son parte del entregable y no un adorno del log:

* `pendientes.md` — qué no se pudo traducir, con su código y la línea del SAS.
* `configuracion-pendiente.md` — qué variable de contexto hay que llenar en cada entorno.
* `decisiones-tomadas.md` — qué eligió el migrador y cómo se cambia.
* `migracion.log` — la causa técnica de cada fallo interno.

Todos se escriben sin fecha ni ruta absoluta: dos corridas sobre el mismo programa dan los mismos
bytes, y eso es lo que permite comparar dos migraciones con `diff`.
"""

from __future__ import annotations

import json
from pathlib import Path

from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.desde_plan_contextos import GRUPOS, PARAMETRO
from sgm.talend_item.modelo import Job, ParametroContexto

SIN_PENDIENTES = "No hay pendientes: todo lo que el programa hace quedó traducido."
SIN_CONFIGURACION = (
    "No hay variables de contexto por completar: el programa no lee ni escribe archivos con ruta."
)
SIN_FALLOS = "Sin fallos internos."


def _celda(texto: str) -> str:
    """Texto de una celda de tabla: sin saltos de línea y con las barras escapadas."""
    return " ".join(str(texto).split()).replace("|", "\\|")


def _tabla(cabecera: list[str], filas: list[list[str]]) -> list[str]:
    lineas = ["| " + " | ".join(cabecera) + " |", "| " + " | ".join("---" for _ in cabecera) + " |"]
    lineas += ["| " + " | ".join(_celda(celda) for celda in fila) + " |" for fila in filas]
    return lineas


def _orden(pendiente: PendienteMigracion) -> tuple[int, str, str]:
    """Orden estable: primero la línea del SAS, después el código y el mensaje."""
    linea = pendiente.linea if pendiente.linea is not None else 10**9
    return (linea, pendiente.codigo, pendiente.mensaje)


def pendientes_md(programa: str, pendientes: list[PendienteMigracion]) -> str:
    lineas = [f"# Pendientes de migración — {programa}", ""]
    if not pendientes:
        return "\n".join([*lineas, SIN_PENDIENTES, ""])
    lineas.append(
        f"{len(pendientes)} pendiente(s). Cada uno dice qué no se pudo demostrar y en qué línea "
        "del programa está: la línea es la que hay que mirar para decidir."
    )
    lineas.append("")
    filas = [
        [f"`{p.codigo}`", str(p.linea) if p.linea is not None else "—", p.mensaje]
        for p in sorted(pendientes, key=_orden)
    ]
    lineas += _tabla(["Código", "Línea", "Motivo"], filas)
    return "\n".join([*lineas, ""])


def _jobs_de(
    contextos: dict[str, list[ParametroContexto]], jobs: list[Job]
) -> dict[str, list[str]]:
    """Variable de contexto -> Jobs que la usan, por el `FILENAME` de sus nodos."""
    usos: dict[str, list[str]] = {
        parametro.nombre: [] for grupo in contextos.values() for parametro in grupo
    }
    for job in jobs:
        for nodo in job.nodos:
            for parametro in nodo.parametros:
                if not isinstance(parametro, tuple) or parametro[1] != PARAMETRO:
                    continue
                valor = str(parametro[2] or "")
                if not valor.startswith("context."):
                    continue
                nombre = valor.removeprefix("context.")
                if nombre in usos and job.nombre not in usos[nombre]:
                    usos[nombre].append(job.nombre)
    return usos


def configuracion_pendiente_md(
    programa: str, contextos: dict[str, list[ParametroContexto]], jobs: list[Job]
) -> str:
    lineas = [f"# Configuración pendiente — {programa}", ""]
    usos = _jobs_de(contextos, jobs)
    vacias = [
        parametro
        for parametro in contextos.get(GRUPOS[0], [])
        if all(
            not next((p.valor for p in contextos[grupo] if p.nombre == parametro.nombre), "")
            for grupo in GRUPOS[1:]
        )
    ]
    if not vacias:
        return "\n".join([*lineas, SIN_CONFIGURACION, ""])
    lineas.append(
        "Estas variables salen vacías en los grupos "
        f"{', '.join(f'`{grupo}`' for grupo in GRUPOS[1:])}: hay que darles el valor de cada "
        "entorno antes de ejecutar el Job. El grupo `Default` trae el valor del SAS y sirve de "
        "referencia."
    )
    lineas.append("")
    filas = [
        [
            f"`{parametro.nombre}`",
            parametro.comentario or "sin descripción",
            ", ".join(f"`{job}`" for job in usos.get(parametro.nombre, [])) or "—",
            ", ".join(GRUPOS[1:]),
        ]
        for parametro in vacias
    ]
    lineas += _tabla(["Variable", "Para qué sirve", "Se usa en", "Grupos"], filas)
    return "\n".join([*lineas, ""])


def _componentes(jobs: list[Job]) -> list[list[str]]:
    return [
        [f"`{job.nombre}`", nodo.componente, f"`{nodo.unico}`", nodo.version]
        for job in jobs
        for nodo in job.nodos
    ]


def decisiones_tomadas_md(
    programa: str, jobs: list[Job], contextos: dict[str, list[ParametroContexto]]
) -> str:
    lineas = [
        f"# Decisiones tomadas — {programa}",
        "",
        "El migrador eligió esto sin preguntar. Cada punto dice cómo cambiarlo si la elección no "
        "sirve para este programa.",
        "",
        "## Qué se eligió",
        "",
        f"* Un Job por cada Job del plan: "
        f"{', '.join(f'`{job.nombre}`' for job in jobs) or 'ninguno'}.",
        "* El componente de cada operador lo decidió el compilador, no este comando: los archivos "
        "se leen con `tFileInputDelimited` o `tFileInputExcel` según el `DBMS` del `PROC IMPORT`, "
        "y las uniones, filtros y columnas calculadas van en un `tMap`.",
        "* Las rutas de archivo no quedan dentro del Job: cada una es una variable `ruta_<tabla>` "
        "con el literal del SAS en el grupo `Default` y vacía en `DEV`, `QA` y `PROD`.",
        "* Las columnas sin tipo demostrado son `String`. Un tipo numérico o una fecha no se "
        "suponen: si el catálogo no lo dice, queda el pendiente `P-TIPO-DESCONOCIDO`.",
        "* La fecha de los `.properties` es la de modificación del programa, no la del reloj: así "
        "dos corridas sobre el mismo archivo dan los mismos bytes.",
        "",
        "## Cómo cambiarlo",
        "",
        "* **Tipos de las columnas**: pasar un catálogo con `--esquemas` o dejar los archivos de "
        "muestra en la carpeta de `--muestra` para que la cabecera dé los nombres.",
        "* **Valores por entorno**: editar `contextos/<grupo>.yaml` y volver a importar el Job; no "
        "hace falta tocar el `.item`.",
        "* **Un operador que no se tradujo**: está en `pendientes.md` con su línea. Mientras no se "
        "resuelva, el Job no hace esa parte y conviene no ejecutarlo en producción.",
        "",
        "## Componentes del Job",
        "",
    ]
    filas = _componentes(jobs)
    lineas += _tabla(["Job", "Componente", "Nodo", "Versión"], filas) if filas else ["Sin nodos."]
    lineas += ["", "## Variables de contexto", ""]
    if contextos.get(GRUPOS[0]):
        lineas += _tabla(
            ["Variable", "Valor por omisión", "Descripción"],
            [
                [f"`{p.nombre}`", f"`{p.valor}`", p.comentario or "—"]
                for p in contextos[GRUPOS[0]]
            ],
        )
    else:
        lineas.append("Sin variables de contexto: el programa no lee ni escribe archivos.")
    return "\n".join([*lineas, ""])


def trace_json(programa: str, jobs: list[Job], traza: dict[str, list[int]]) -> str:
    """Nodo del Job -> líneas del SAS que lo originaron, agrupado por Job."""
    contenido = {
        "programa": programa,
        "jobs": {
            job.nombre: {
                nodo.unico: traza[nodo.unico]
                for nodo in job.nodos
                if nodo.unico in traza
            }
            for job in jobs
        },
    }
    return json.dumps(contenido, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def migracion_log(notas: list[str]) -> str:
    """Causas técnicas de los fallos internos, en el orden en que ocurrieron."""
    if not notas:
        return SIN_FALLOS + "\n"
    return "\n".join(notas) + "\n"


def escribir(carpeta: Path, nombre: str, contenido: str) -> Path:
    """Escribe un archivo de texto con salto de línea `\\n`, creando la carpeta si falta."""
    ruta = carpeta / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    return ruta


__all__ = [
    "configuracion_pendiente_md",
    "decisiones_tomadas_md",
    "escribir",
    "migracion_log",
    "pendientes_md",
    "trace_json",
]
