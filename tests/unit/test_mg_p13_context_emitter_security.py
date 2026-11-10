"""Validación de nombres de contexto usados por emisores y decisiones."""

from __future__ import annotations

import pytest

from sgm.proceso.insumos import InsumoResuelto, InsumosResueltos
from sgm.talend_item.arquitectura import (
    Arquitectura,
    PeriodoDecl,
    cargar_arquitectura,
)
from sgm.talend_item.jobs_diseno import job_pendiente
from sgm.talend_item.jobs_producto import job_producto
from sgm.talend_item.jobs_totales import variables_fecha
from sgm.talend_item.periodo import nodos_periodo


def test_job_pendiente_rechaza_nombre_de_contexto_con_sintaxis_java():
    with pytest.raises(ValueError, match="identificador de contexto"):
        job_pendiente("job", "falta dato", ("periodo;System.exit(1)//",))


def test_job_producto_rechaza_nombre_de_contexto_con_sintaxis_java():
    arq = Arquitectura("P", ("DEV",), "padre", "producto", "totales", "conc", "fin")

    with pytest.raises(ValueError, match="identificador de contexto"):
        job_producto(arq, ("A",), variables_periodo=("periodo;System.exit(1)//",))


def test_decision_rechaza_nombre_de_contexto_invalido_sin_reproducirlo(tmp_path):
    archivo = tmp_path / "programa.jobs.yaml"
    archivo.write_text(
        "proyecto: P\nentornos: [DEV]\n"
        "jobs: {padre: padre, producto: producto, totales: totales, conciliacion: conc}\n"
        "periodo:\n  fuente: fecha\n  variables: {ANIO: 'periodo;System.exit(1)//'}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="identificador de contexto") as error:
        cargar_arquitectura(archivo)
    assert "System.exit" not in str(error.value)


def test_nodos_periodo_rechaza_nombre_de_contexto_no_portable():
    arq = Arquitectura(
        "P",
        ("DEV",),
        "padre",
        "producto",
        "totales",
        "conc",
        "fin",
        periodo=PeriodoDecl("fecha", (("ANIO", "periodo;System.exit(1)//"),)),
    )
    insumo = InsumoResuelto(
        "fecha", "fecha.xlsx", "C:/", "fecha.xlsx", "ruta", "archivo", ("ANIO",)
    )

    with pytest.raises(ValueError, match="identificador de contexto"):
        nodos_periodo(arq, InsumosResueltos({"fecha": insumo}))


def test_variables_fecha_rechaza_nombre_de_contexto_no_portable():
    arq = Arquitectura(
        "P",
        ("DEV",),
        "padre",
        "producto",
        "totales",
        "conc",
        "fin",
        periodo=PeriodoDecl(
            "fecha", (("AÑO", "anio;System.exit(1)//"), ("MES", "mes"), ("DIA", "dia"))
        ),
    )

    with pytest.raises(ValueError, match="identificador de contexto"):
        variables_fecha(arq)
