"""Tests de `sgm flujo`: pasos, datasets que pasan de uno a otro, capas, seguridad y HTML."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from sgm.flow.layout import render_svg
from sgm.flow.model import build_flows
from sgm.flow.page import render_page

PROGRAMA = """\
%let ruta = /datos;
libname entrada "&ruta.";
data trabajo.clientes;
  set entrada.clientes;
  where activo = 1;
run;
proc sql;
  create table resumen as
  select cuenta, count(*) as n from trabajo.clientes group by cuenta;
quit;
proc sort data=resumen;
  by cuenta;
run;
"""


def _flow(texto: str, nombre: str = "p.sas"):
    return build_flows({nombre: texto})[nombre]


def test_pasos_y_datasets_de_cada_paso():
    flujo = _flow(PROGRAMA)
    assert [s.type_name for s in flujo.steps] == ["DATA step", "PROC SQL", "PROC SORT"]
    data, sql, sort = flujo.steps
    assert data.reads == ["entrada.clientes"] and data.writes == ["trabajo.clientes"]
    assert sql.reads == ["trabajo.clientes"] and sql.writes == ["resumen"]
    assert sort.reads == ["resumen"] and sort.writes == ["resumen"]
    assert "ordena el dataset en su lugar (sin OUT=)" in sort.notes


def test_cada_lectura_se_une_al_ultimo_paso_que_escribio_el_dataset():
    flujo = _flow(PROGRAMA)
    pares = {(e.source, e.target, e.dataset) for e in flujo.edges}
    entrada = flujo.inputs[0].id
    assert (entrada, "p1", "entrada.clientes") in pares
    assert ("p1", "p2", "trabajo.clientes") in pares
    assert ("p2", "p3", "resumen") in pares
    assert flujo.external_inputs == ["entrada.clientes"]


def test_capas_avanzan_con_las_dependencias():
    flujo = _flow(PROGRAMA)
    capas = {s.id: s.layer for s in flujo.steps}
    assert capas["p1"] < capas["p2"] < capas["p3"]


def test_work_y_sin_prefijo_son_el_mismo_dataset():
    texto = "data work.x; set origen; run;\nproc print data=x; run;\n"
    flujo = _flow(texto)
    assert [(e.source, e.target) for e in flujo.edges if e.target == "p2"] == [("p1", "p2")]


def test_configuracion_se_separa_de_los_pasos():
    flujo = _flow(PROGRAMA)
    tipos = [c.kind for c in flujo.config]
    assert "%let" in tipos and "libname" in tipos
    assert all(s.kind != "config" for s in flujo.steps)


def test_credenciales_no_llegan_al_html():
    texto = (
        "proc pwencode in='Secreto123' out=salida; run;\n"
        "libname bd odbc dsn=x user=ana password=ClaveSecreta;\n"
        "data a; set bd.tabla; run;\n"
    )
    flujo = _flow(texto)
    html = render_page(flujo)
    assert "Secreto123" not in html
    assert "ClaveSecreta" not in html


def test_texto_del_programa_se_escapa():
    texto = 'data a; set b; put "<script>alert(1)</script>"; run;\n'
    html = render_page(_flow(texto))
    assert "<script>alert" not in html


def test_svg_es_xml_bien_formado_y_tiene_una_caja_por_paso():
    flujo = _flow(PROGRAMA)
    svg = render_svg(flujo)
    ET.fromstring(svg)  # lanza si no es XML válido
    assert svg.count('class="nodo ') == len(flujo.steps) + len(flujo.inputs)


def test_programa_sin_pasos_renderiza_mensaje():
    flujo = _flow("%let a = 1;\n")
    assert flujo.steps == []
    html = render_page(flujo)
    assert "no tiene pasos de datos" in html
    ET.fromstring(render_svg(flujo))


def test_macro_se_expande_y_conserva_su_llamada():
    texto = "%macro m(x); data &x; set y; run; %mend;\n%let t = z;\n%m(&t.);\n"
    flujo = _flow(texto)
    assert [s.title for s in flujo.steps] == ["DATA z"]
    assert flujo.steps[0].macro_call.endswith(":m")
    assert flujo.steps[0].reads == ["y"]


def test_bloque_condicional_no_constante_es_macro_dinamica_pendiente():
    texto = "%if %sysfunc(exist(x)) %then %do;\n data a; set b; run;\n%end;\n"
    flujo = _flow(texto)
    dinamicos = [s for s in flujo.steps if s.kind == "dynamic"]
    assert len(dinamicos) == 1
    assert "ejecutar" in dinamicos[0].notes[0]
    assert any("p.sas:1" in p.text for p in flujo.pending)
