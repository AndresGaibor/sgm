"""`job_conciliacion` real (hito 98d, R2-03): cruce origen contra salida, chequeo y `tDie`."""

from __future__ import annotations

import pytest

from sgm.talend_item.arquitectura import Arquitectura, PeriodoDecl
from sgm.talend_item.jobs_conciliacion import (
    CODIGO_NO_CONCILIA,
    MENSAJE,
    TOLERANCIA,
    job_conciliacion,
)
from sgm.talend_item.jobs_diseno import jobs_hijos
from sgm.talend_item.modelo import Job, Nodo

PERIODO = PeriodoDecl(
    "Validación de fecha",
    (("AÑO", "periodo_anio"), ("MES", "periodo_mes"), ("DIA", "periodo_dia")),
)


def _arq(periodo: PeriodoDecl | None = PERIODO, archivo: str = "totales_exogena") -> Arquitectura:
    return Arquitectura(
        proyecto="PRJ",
        entornos=("DEV",),
        padre="job_padre",
        producto="job_producto",
        totales="job_totales",
        conciliacion="job_conciliacion",
        mensaje_fin="fin",
        periodo=periodo,
        archivo_totales=archivo,
    )


def _valor(nodo: Nodo, nombre: str) -> str:
    return next(v for _, n, v, _ in nodo.parametros if n == nombre)


def _por_nombre(job: Job) -> dict[str, Nodo]:
    return {n.unico: n for n in job.nodos}


def test_cada_producto_tiene_dos_lectores_un_cruce_y_una_escritura():
    job = job_conciliacion(_arq(), ("CTE", "AHO"))
    componentes = [n.componente for n in job.nodos]
    assert componentes.count("tFileInputDelimited") == 2 * 2 + 1  # origen y salida, más chequeo
    assert componentes.count("tMap") == 2
    assert componentes.count("tFileOutputDelimited") == 2
    assert componentes.count("tDie") == 1


def test_los_lectores_de_totales_hacen_fallar_el_job_si_no_leen():
    job = job_conciliacion(_arq(), ("CTE", "AHO"))
    lectores = [n for n in job.nodos if n.componente == "tFileInputDelimited"]
    assert lectores and all(_valor(n, "DIE_ON_ERROR") == "true" for n in lectores)


def test_origen_y_salida_de_cada_producto_son_los_archivos_de_totales():
    job = job_conciliacion(_arq(), ("CTE",))
    rutas = [_valor(n, "FILENAME") for n in job.nodos if n.componente == "tFileInputDelimited"]
    assert '"totales_origen_CTE.csv"' in rutas[0]
    assert '"totales_salida_CTE.csv"' in rutas[1]


def test_el_cruce_usa_el_producto_como_clave_de_lookup():
    job = job_conciliacion(_arq(), ("CTE",))
    cruce = _por_nombre(job)["tMap_1"]
    assert "tMap" in cruce.componente
    lookups = [c for c in job.conexiones if c.conector == "LOOKUP"]
    assert [(c.origen, c.destino) for c in lookups] == [
        ("tFileInputDelimited_s1", "tMap_1")
    ]


def test_la_salida_tiene_las_columnas_de_conciliacion_final_del_sas():
    job = job_conciliacion(_arq(), ("CTE",))
    escritura = _por_nombre(job)["tFileOutputDelimited_1"]
    columnas = [c.nombre for c in escritura.metadatas[0].columnas]
    assert columnas == ["PRODUCTO", "DIF_FILAS", "DIF_SALDO"]


def test_el_archivo_lleva_la_fecha_del_periodo_y_la_cabecera_solo_en_el_primero():
    job = job_conciliacion(_arq(), ("CTE", "AHO"))
    salidas = [n for n in job.nodos if n.componente == "tFileOutputDelimited"]
    destino = _valor(salidas[0], "FILENAME")
    assert '"conciliacion_"' in destino
    assert "context.periodo_anio" in destino and "context.periodo_dia" in destino
    assert [_valor(n, "INCLUDEHEADER") for n in salidas] == ["true", "false"]
    assert [_valor(n, "APPEND") for n in salidas] == ["false", "true"]


def test_la_tolerancia_es_contexto_con_omision_cero():
    job = job_conciliacion(_arq(), ("CTE",))
    tolerancia = next(p for p in job.contextos["Default"] if p.nombre == TOLERANCIA)
    assert tolerancia.valor == "0"
    assert "confirmar con negocio" in tolerancia.comentario


def test_el_chequeo_relee_el_archivo_y_marca_no_concilia_con_filas_exactas():
    job = job_conciliacion(_arq(), ("CTE",))
    marca = _por_nombre(job)["tJavaRow_chk"]
    codigo = _valor(marca, "CODE")
    assert "dif != 0" in codigo
    assert "compareTo(tol) > 0" in codigo
    assert f'globalMap.put("{MENSAJE}"' in codigo


def test_tdie_sale_con_codigo_numerico_y_mensaje_de_globalmap():
    job = job_conciliacion(_arq(), ("CTE",))
    fallo = _por_nombre(job)["tDie_conc"]
    assert _valor(fallo, "EXIT_JVM") == "true"
    assert _valor(fallo, "CODE") == str(CODIGO_NO_CONCILIA)
    assert f'globalMap.get("{MENSAJE}")' in _valor(fallo, "MESSAGE")
    condiciones = [c for c in job.conexiones if c.conector == "RUN_IF"]
    assert [(c.origen, c.destino) for c in condiciones] == [("tJavaRow_chk", "tDie_conc")]


def test_los_productos_van_en_subjobs_en_orden():
    job = job_conciliacion(_arq(), ("CTE", "AHO"))
    disparadores = [(c.origen, c.destino) for c in job.conexiones if c.conector == "SUBJOB_OK"]
    assert disparadores == [
        ("tJava_1", "tFileInputDelimited_o1"),
        ("tFileInputDelimited_o1", "tFileInputDelimited_o2"),
        ("tFileInputDelimited_o2", "tFileInputDelimited_chk"),
    ]


def test_el_nombre_puede_cambiarse_para_las_pruebas():
    assert job_conciliacion(_arq(), ("CTE",), nombre="caso_conc").nombre == "caso_conc"
    assert job_conciliacion(_arq(), ("CTE",)).nombre == "job_conciliacion"


@pytest.mark.parametrize(
    ("productos", "periodo", "archivo", "motivo"),
    [
        ((), PERIODO, "totales_exogena", "al menos un producto"),
        (("CTE",), PERIODO, "", "archivo_totales"),
        (("CTE",), None, "totales_exogena", "AÑO"),
    ],
)
def test_sin_productos_archivo_o_periodo_no_hay_job(productos, periodo, archivo, motivo):
    with pytest.raises(ValueError, match=motivo):
        job_conciliacion(_arq(periodo, archivo), productos)


def test_jobs_hijos_usa_la_conciliacion_real_si_se_entrega():
    real = job_conciliacion(_arq(), ("CTE",))
    hijos = jobs_hijos(_arq(), conciliacion_real=real)
    assert hijos[2] is real
    pendiente = jobs_hijos(_arq())[2]
    assert pendiente.nodos[0].componente == "tJava"
