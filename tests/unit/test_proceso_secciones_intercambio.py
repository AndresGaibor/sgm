"""Tests de las secciones 1.2 (intercambio de totales y lookups) y 1.3 (variables del periodo)."""

from __future__ import annotations

from sgm.proceso.secciones_entrada import ORIGEN_DECLARADA, ORIGEN_SAS
from sgm.proceso.secciones_intercambio import seccion_intercambio, seccion_periodo
from sgm.talend_item.arquitectura import Arquitectura, PeriodoDecl


def _arquitectura(archivo_totales: str = "totales_exogena") -> Arquitectura:
    return Arquitectura(
        proyecto="PRJ",
        entornos=("DEV",),
        padre="job_exogena_depositos",
        producto="job_producto",
        totales="job_totales",
        conciliacion="job_conciliacion",
        mensaje_fin="Proceso terminado",
        periodo=PeriodoDecl(
            "Validación de fecha", (("AÑO", "periodo_anio"), ("MES", "periodo_mes"))
        ),
        archivo_totales=archivo_totales,
    )


def test_intercambio_toma_las_columnas_declaradas_y_marca_declarada() -> None:
    declarados = [
        {"clave": "totales_origen_cte", "creada_en": "job_producto (CTE)", "leida_en": "job_totales"}
    ]
    seccion, origenes = seccion_intercambio(declarados)
    assert seccion == {
        "totales_origen_cte": {
            "creada_en": "job_producto (CTE)",
            "leida_en": "job_totales",
            "contenido": "pendiente",
            "clave_busqueda": "pendiente",
        }
    }
    assert origenes == {"totales_origen_cte": ORIGEN_DECLARADA}


def test_intercambio_sin_declaraciones_no_inventa_filas() -> None:
    assert seccion_intercambio([]) == ({}, {})


def test_periodo_una_fila_por_variable_creada_por_el_padre() -> None:
    seccion, origenes = seccion_periodo(_arquitectura(), ORIGEN_SAS)
    assert set(seccion) == {"periodo_anio", "periodo_mes"}
    anio = seccion["periodo_anio"]
    assert anio["creada_en"] == "job_exogena_depositos (padre)"
    assert anio["origen"] == "Columna AÑO de «Validación de fecha»"
    assert "totales_exogena" in anio["uso"]
    assert origenes == {"periodo_anio": ORIGEN_SAS, "periodo_mes": ORIGEN_SAS}


def test_periodo_sin_archivo_de_totales_dice_que_falta_el_uso() -> None:
    seccion, _ = seccion_periodo(_arquitectura(archivo_totales=""), ORIGEN_DECLARADA)
    assert seccion["periodo_mes"]["uso"].startswith("Pendiente:")


def test_sin_periodo_declarado_la_seccion_queda_vacia() -> None:
    assert seccion_periodo(None, ORIGEN_SAS) == ({}, {})
