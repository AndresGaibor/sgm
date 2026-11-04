"""Tests de fuentes, persistencias, pendientes y plantillas de salida."""

from __future__ import annotations

from sgm.flow.model import build_flows
from sgm.proceso.entradas_salidas import entradas_y_salidas

PRODUCTOS = {"cte": ("CTE",), "aho": ("AHO",)}

PROGRAMA = """\
proc import datafile="/in/lookup.xlsx" out=work.lk dbms=xlsx replace; run;
proc import datafile="/in/datos.csv" out=work.d dbms=csv replace; run;
proc sql;
connect to impala (dsn=x);
create table work.base_cte as
  select * from connection to impala (select a from esq.origen_tabla);
disconnect from impala;
quit;
data work.sabana_cte; set work.base_cte; run;
data work.sabana_aho; set work.base_cte; run;
data work.final; set lz.sabana_cte lz.otra_externa work.nunca_escrita work.&dinamica.; run;
proc export data=work.sabana_cte outfile="/out/RESULTADO_CTE.csv" dbms=csv replace; run;
proc export data=work.sabana_aho outfile="/out/RESULTADO_AHO.csv" dbms=csv replace; run;
proc export data=work.final outfile="/out/TOTAL.csv" dbms=csv replace; run;
"""


def _resultado():
    modelo = build_flows({"p.sas": PROGRAMA})["p.sas"]
    return entradas_y_salidas(modelo, PRODUCTOS)


def test_archivos_se_clasifican_por_extension_y_las_tablas_de_base_son_fuentes():
    res = _resultado()
    tipos = {(f.tipo, f.ubicacion) for f in res.fuentes}
    assert ("excel", "/in/lookup.xlsx") in tipos
    assert ("csv", "/in/datos.csv") in tipos
    assert ("tabla_base", "esq.origen_tabla") in tipos
    assert ("tabla_base", "lz.otra_externa") in tipos


def test_tabla_de_base_con_el_nombre_de_un_work_escrito_es_persistencia_propia():
    res = _resultado()
    assert res.persistidas == ["lz.sabana_cte"]
    assert all(f.ubicacion != "lz.sabana_cte" for f in res.fuentes)


def test_nombres_sin_resolver_y_work_sin_escritor_quedan_pendientes_con_motivo():
    res = _resultado()
    motivos = {p.nombre.lower(): p.motivo for p in res.pendientes}
    assert "macrovariable" in motivos["work.&dinamica."]
    assert "antes" in motivos["work.nunca_escrita"]


def test_las_salidas_se_agrupan_por_plantilla_con_producto_como_parametro():
    res = _resultado()
    por_plantilla = {p.plantilla: p.instancias for p in res.salidas}
    assert por_plantilla["RESULTADO_{P}.csv"] == (
        ("cte", "/out/RESULTADO_CTE.csv"),
        ("aho", "/out/RESULTADO_AHO.csv"),
    )
    assert por_plantilla["TOTAL.csv"] == ((None, "/out/TOTAL.csv"),)
