"""Línea base de la conformidad: cuántas filas del manual salen hoy del SAS.

Los números son los que mide `sgm conformidad tests/fixtures/sas/client/client_large.sas`
(hito 93; sección 2.1 y el alta de las filas X03, X04, X05 y X07 en el hito 94). Si un cambio baja
las derivadas, esta prueba falla: hay que explicar por qué antes de cambiar la cifra. Si sube,
también falla, para dejar constancia en `PROGRESS.md`.
"""

from __future__ import annotations

from functools import lru_cache

from sgm.conformidad import informe
from sgm.conformidad.estado import clasificar_filas
from sgm.conformidad.referencia import cargar_secciones
from sgm.proceso.diseno_doc import SECCIONES_EMITIDAS, construir_documento
from tests.conformidad.cargador import RAIZ

PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
DECISIONES = RAIZ / "decisiones"

TOTAL_FILAS = 118
DERIVADAS = ["F01", "F02", "F03", "F05", "S03", "X03", "X04", "X05", "X07"]
DIFERENCIAS = ["F04", "X01", "X06"]


@lru_cache(maxsize=1)
def _resumen() -> dict:
    doc = construir_documento(
        PROGRAMA,
        DECISIONES / f"{PROGRAMA.stem}.agrupacion.yaml",
        DECISIONES / f"{PROGRAMA.stem}.diseno.yaml",
    )
    filas = clasificar_filas(cargar_secciones(), doc.secciones, doc.origenes, SECCIONES_EMITIDAS)
    return {"resumen": informe.resumir(filas), "filas": filas}


def test_total_de_filas_de_la_referencia() -> None:
    assert _resumen()["resumen"]["total"] == TOTAL_FILAS


def test_filas_derivadas_del_sas_son_la_linea_base() -> None:
    derivadas = [f.id for f in _resumen()["filas"] if f.estado == "derivada"]
    assert derivadas == DERIVADAS


def test_unica_diferencia_medida_es_la_conocida() -> None:
    diferencias = [d["id"] for d in _resumen()["resumen"]["diferencias"]]
    assert diferencias == DIFERENCIAS
