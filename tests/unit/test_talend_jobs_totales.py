"""`job_totales` real (hito 97, R2-02): une los totales por producto y escribe la exógena."""

from __future__ import annotations

import dataclasses

import pytest

from sgm.talend_item.arquitectura import Arquitectura, PeriodoDecl
from sgm.talend_item.jobs_diseno import jobs_hijos
from sgm.talend_item.jobs_totales import COLUMNAS_TOTALES, job_totales, variables_fecha
from sgm.talend_item.modelo import Job, Nodo


def _arq(periodo: PeriodoDecl | None = None) -> Arquitectura:
    return Arquitectura(
        proyecto="PRJ",
        entornos=("DEV",),
        padre="job_padre",
        producto="job_producto",
        totales="job_totales",
        conciliacion="job_conciliacion",
        mensaje_fin="fin",
        periodo=periodo,
        archivo_totales="totales_exogena",
    )


PERIODO = PeriodoDecl(
    "Validación de fecha",
    (("AÑO", "periodo_anio"), ("MES", "periodo_mes"), ("DIA", "periodo_dia")),
)


def _valor(nodo: Nodo, nombre: str) -> str:
    return next(v for _, n, v, _ in nodo.parametros if n == nombre)


def _por_nombre(job: Job) -> dict[str, Nodo]:
    return {n.unico: n for n in job.nodos}


def test_une_origen_y_salida_de_cada_producto_en_orden_de_subjobs():
    job = job_totales(_arq(PERIODO), ("CTE", "AHO"))
    nodos = _por_nombre(job)
    entradas = [nodos[f"tFileInputDelimited_{i}"] for i in range(1, 5)]
    rutas = [_valor(n, "FILENAME") for n in entradas]
    assert "totales_origen_CTE.csv" in rutas[0]
    assert "totales_salida_CTE.csv" in rutas[1]
    assert "totales_origen_AHO.csv" in rutas[2]
    assert "totales_salida_AHO.csv" in rutas[3]
    # Cada entrada arranca cuando termina la anterior: OnSubjobOk con ordinal creciente.
    disparadores = [c for c in job.conexiones if c.conector == "SUBJOB_OK"]
    assert [(c.origen, c.destino) for c in disparadores] == [
        ("tJava_1", "tFileInputDelimited_1"),
        ("tFileInputDelimited_1", "tFileInputDelimited_2"),
        ("tFileInputDelimited_2", "tFileInputDelimited_3"),
        ("tFileInputDelimited_3", "tFileInputDelimited_4"),
    ]


def test_solo_el_primer_archivo_escribe_cabecera_y_los_demas_añaden():
    job = job_totales(_arq(PERIODO), ("CTE", "AHO"))
    salidas = [n for n in job.nodos if n.componente == "tFileOutputDelimited"]
    assert [_valor(n, "APPEND") for n in salidas] == ["false", "true", "true", "true"]
    assert [_valor(n, "INCLUDEHEADER") for n in salidas] == ["true", "false", "false", "false"]


def test_la_exogena_lleva_la_fecha_del_periodo_en_el_nombre():
    job = job_totales(_arq(PERIODO), ("CTE",))
    salida = _por_nombre(job)["tFileOutputDelimited_1"]
    destino = _valor(salida, "FILENAME")
    assert '"totales_exogena_"' in destino
    assert "context.periodo_anio" in destino
    assert "context.periodo_mes" in destino
    assert "context.periodo_dia" in destino


def test_el_contexto_declara_la_ruta_de_resultados_y_las_variables_de_fecha():
    job = job_totales(_arq(PERIODO), ("CTE",))
    nombres = [p.nombre for p in job.contextos["Default"]]
    assert nombres == ["ruta_resultados", "periodo_anio", "periodo_mes", "periodo_dia"]


def test_las_entradas_fallan_si_el_archivo_no_se_puede_leer():
    job = job_totales(_arq(PERIODO), ("CTE",))
    entrada = _por_nombre(job)["tFileInputDelimited_1"]
    assert _valor(entrada, "DIE_ON_ERROR") == "true"


def test_no_usa_tunite_porque_no_compila_en_studio():
    job = job_totales(_arq(PERIODO), ("CTE", "AHO"))
    assert all(n.componente != "tUnite" for n in job.nodos)


def test_las_columnas_son_las_de_la_exogena_en_todas_las_entradas_y_salidas():
    job = job_totales(_arq(PERIODO), ("CTE",))
    for nodo in job.nodos:
        if nodo.componente in {"tFileInputDelimited", "tFileOutputDelimited"}:
            flujo = nodo.metadatas[0].columnas
            assert [c.nombre for c in flujo] == [c.nombre for c in COLUMNAS_TOTALES]


def test_sin_periodo_declarado_falla_con_el_motivo():
    with pytest.raises(ValueError, match="periodo declarado"):
        job_totales(_arq(None), ("CTE",))


def test_un_periodo_sin_dia_falla_con_el_nombre_que_falta():
    incompleto = PeriodoDecl("Validación de fecha", (("AÑO", "a"), ("MES", "m")))
    with pytest.raises(ValueError, match="dia"):
        variables_fecha(_arq(incompleto))


def test_sin_productos_no_hay_job():
    with pytest.raises(ValueError, match="al menos un producto"):
        job_totales(_arq(PERIODO), ())


def test_jobs_hijos_usa_el_job_de_totales_real_si_se_le_pasa():
    arq = _arq(PERIODO)
    real = job_totales(arq, ("CTE",))
    hijos = {j.nombre: j for j in jobs_hijos(arq, totales_real=real)}
    assert hijos["job_totales"] is real


def test_sin_archivo_totales_falla_con_el_motivo():
    arq = dataclasses.replace(_arq(PERIODO), archivo_totales="")
    with pytest.raises(ValueError, match="archivo_totales"):
        job_totales(arq, ("CTE",))
