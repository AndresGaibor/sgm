"""Hito 91 / R1-05: la rama de ubicación llega al `job_producto` emitido, y solo con la regla.

Sin Studio: `sgm talend` sobre `client_large.sas` no emite la rama (su SAS no tiene la forma del
caso v03) y publica el pendiente; con la regla de v03 la rama añade cinco componentes (un `tMap`,
dos lookups Excel y dos CSV) y las conexiones salen de `tReplicate_1` sin repetir nombres.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))

from sgm.cli_talend import _ubicacion  # noqa: E402
from sgm.proceso.reglas_ubicacion import reglas_ubicacion  # noqa: E402
from sgm.talend_item.arquitectura import cargar_arquitectura  # noqa: E402
from sgm.talend_item.flujos_ubicacion import EXCEL, SALIDA, TMAP, componentes  # noqa: E402
from sgm.talend_item.jobs_producto import UBICACION_PARAMETROS, job_producto  # noqa: E402
from sgm.talend_item.modelo import Columna  # noqa: E402

PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
V03 = RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v03_pais_dane" / "programa.sas"
TEXTO_CLIENTE = PROGRAMA.read_text(encoding="utf-8", errors="replace")
TEXTO_V03 = V03.read_text(encoding="utf-8", errors="replace")
REGLA = reglas_ubicacion(TEXTO_V03)
ARQ = cargar_arquitectura(RAIZ / "decisiones" / "client_large.jobs.yaml")
COLUMNAS = (
    "LLAVE_NOMBRE", "RELACION", "TIPO_DOC", "NRO_DOC", "PAIS", "CODIGO_UBICACION", "DIRECCION",
)  # fmt: skip


def _job(ubicacion=None, columnas=COLUMNAS):
    return job_producto(ARQ, columnas, ubicacion=ubicacion)


def test_el_programa_de_cliente_no_emite_la_rama_y_publica_el_pendiente():
    regla, avisos = _ubicacion(TEXTO_CLIENTE)
    assert regla is None
    assert len(avisos) == 1
    assert avisos[0].startswith("R1-05: no se emite la ubicación")


def test_la_regla_de_v03_trae_sus_pendientes_al_cli():
    regla, avisos = _ubicacion(TEXTO_V03)
    assert regla is not None
    assert list(avisos) == list(REGLA.pendientes)


def test_la_rama_agrega_cinco_componentes_al_job():
    base = _job()
    con = _job(REGLA)
    assert len(con.nodos) == len(base.nodos) + 5
    nombres = {n.unico for n in con.nodos}
    assert {TMAP, EXCEL["pais"], EXCEL["dane"]} <= nombres


def test_las_conexiones_de_la_rama_tienen_nombres_propios_y_unicos():
    # `row1` se repite a propósito en el resto del Job; las de la rama deben llevar `ubic_`.
    con = _job(REGLA)
    propias = [c.nombre for c in con.conexiones if c.nombre.startswith("ubic_")]
    assert sorted(propias) == sorted(["ubic_fuente", "ubic_pais", "ubic_dane", "ubic_rechazo", "ubic_valida"])


def test_los_lookups_son_left_join_sin_inner():
    nodos, conexiones = componentes(REGLA, [Columna(c) for c in COLUMNAS])
    tmap = next(n for n in nodos if n.unico == TMAP)
    # El SAS une con LEFT JOIN: ningún lookup lleva `innerJoin`, y los dos sí llevan su unión.
    assert "innerJoin" not in tmap.datos
    lookups = [c for c in conexiones if c.estilo == 8]
    assert len(lookups) == 2
    assert {c.origen for c in lookups} == {EXCEL["pais"], EXCEL["dane"]}
    assert 'name="ubic_pais"' in tmap.datos and 'name="ubic_dane"' in tmap.datos


def test_las_salidas_csv_llevan_cabecera_y_sufijo():
    nodos, _ = componentes(REGLA, [Columna(c) for c in COLUMNAS])
    csv = [n for n in nodos if n.componente == "tFileOutputDelimited"]
    assert len(csv) == 2
    assert {n.unico for n in csv} == {SALIDA.format(n=1), SALIDA.format(n=2)}


def test_la_rama_pide_la_sabana_con_ubicacion_y_falla_sin_ella():
    sin = tuple(c for c in COLUMNAS if c != "DIRECCION")
    with pytest.raises(ValueError):
        _job(REGLA, sin)


def test_los_parametros_de_ubicacion_van_al_contexto_con_el_valor_del_sas():
    job = _job(REGLA)
    contexto = {p.nombre: p.valor for p in job.contextos["Default"]}
    for nombre in UBICACION_PARAMETROS:
        assert nombre in contexto
    assert contexto["arch_hom_pais"] == "Cod_pais.xlsx"
    assert contexto["arch_hom_dane"] == "CODIGOS_DANE.xlsx"


def test_sin_regla_el_job_no_cambia():
    assert [n.unico for n in _job(None).nodos] == [n.unico for n in _job().nodos]
