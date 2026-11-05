"""Secciones 1.2 (intercambio de datos entre Jobs) y 1.3 (variables del periodo) del documento.

La 1.2 sale de `decisiones/<programa>.diseno.yaml` (clave `intercambios`). El SAS no tiene cachés:
el texto lo fija el emisor y su evidencia está en `PROGRESS.md`; por eso su origen es `declarada`.
La 1.3 sale del modelo de Jobs (`decisiones/<programa>.jobs.yaml`): el padre lee la fecha de su
Excel y la pasa a los hijos por variables de contexto. No hay Job intermedio que la lea.
"""

from __future__ import annotations

from sgm.proceso.secciones_entrada import ORIGEN_DECLARADA
from sgm.talend_item.arquitectura import Arquitectura

Fila = dict[str, str]
Seccion = dict[str, Fila]
CAMPOS_INTERCAMBIO = ("creada_en", "leida_en", "contenido", "clave_busqueda")


def seccion_intercambio(declarados: list[dict[str, str]]) -> tuple[Seccion, dict[str, str]]:
    """Sección 1.2: cada lookup o archivo de totales, con quién lo crea y quién lo lee."""
    seccion: Seccion = {}
    origenes: dict[str, str] = {}
    for d in declarados:
        seccion[d["clave"]] = {campo: d.get(campo, "pendiente") for campo in CAMPOS_INTERCAMBIO}
        origenes[d["clave"]] = ORIGEN_DECLARADA
    return seccion, origenes


def _uso_periodo(arq: Arquitectura) -> str:
    if arq.archivo_totales:
        return f"Fecha en el nombre del archivo de totales ({arq.archivo_totales}_<anio><mes><dia>)"
    return "Pendiente: no hay archivo de totales declarado para usar la fecha"


def seccion_periodo(arq: Arquitectura | None, origen_fuente: str) -> tuple[Seccion, dict[str, str]]:
    """Sección 1.3: una fila por variable de periodo que el padre deja en el contexto.

    `origen_fuente` es `sas` si el Excel de la fecha se halla en el programa, o `declarada`.
    """
    if arq is None or arq.periodo is None:
        return {}, {}
    seccion: Seccion = {}
    origenes: dict[str, str] = {}
    for columna, variable in arq.periodo.variables:
        seccion[variable] = {
            "creada_en": f"{arq.padre} (padre)",
            "origen": f"Columna {columna} de «{arq.periodo.fuente}»",
            "uso": _uso_periodo(arq),
        }
        origenes[variable] = origen_fuente
    return seccion, origenes
