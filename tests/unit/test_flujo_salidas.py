"""Pruebas de las salidas de `sgm flujo`: índice de datasets, JSON, vista por sección, HTML y casos límite."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from sgm.cli_flow import flujo_command
from sgm.flow.layout import positions, render_svg
from sgm.flow.model import FlowModel, FlowStep, build_flows
from sgm.flow.page import render_page
from sgm.flow.salida import a_json, indice_datasets, salidas_finales
from sgm.flow.seccion import SECCION_MAX_PASOS, _tramos, by_section
from sgm.flow.texto import es_dinamico, etiqueta_paso, frase_resumen

REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "tests" / "fixtures" / "flujo" / "p1_merge_first_last.flujo.html"
FECHA = re.compile(r"Generado el \d{4}-\d{2}-\d{2}")

PROGRAMA = """\
data trabajo.clientes;
  set entrada.clientes;
run;
proc sql;
  create table resumen as select cuenta from trabajo.clientes;
quit;
proc sort data=resumen;
  by cuenta;
run;
"""


def _flujo(texto: str, nombre: str = "p.sas") -> FlowModel:
    return build_flows({nombre: texto})[nombre]


def _paso(nombre: str, escribe: str | None, etiqueta: str = "S") -> FlowStep:
    return FlowStep(
        id=nombre,
        file="p.sas",
        line=1,
        label=etiqueta,
        kind="data",
        type_name="DATA step",
        title=nombre,
        writes=[escribe] if escribe else [],
    )


def test_indice_de_datasets_lista_quien_escribe_y_quien_lee():
    usos = {u.nombre: u for u in indice_datasets(_flujo(PROGRAMA))}
    assert usos["trabajo.clientes"].escriben == ["p1"]
    assert usos["trabajo.clientes"].leen == ["p2"]
    # PROC SORT sin OUT= ordena en su lugar: también escribe `resumen`.
    assert usos["resumen"].escriben == ["p2", "p3"]
    assert usos["resumen"].leen == ["p3"]


def test_json_tiene_version_pasos_conexiones_y_pendientes():
    datos = json.loads(a_json(_flujo(PROGRAMA)))
    assert datos["version"] == 1
    assert [p["id"] for p in datos["pasos"]] == ["p1", "p2", "p3"]
    assert len(datos["conexiones"]) == 3
    assert datos["entradas_externas"] == ["entrada.clientes"]


def test_pendiente_de_macro_dinamica_enlaza_con_su_paso():
    flujo = _flujo("%if %sysfunc(exist(x)) %then %do;\n data a; set b; run;\n%end;\n")
    dinamico = next(s for s in flujo.steps if s.kind == "dynamic")
    enlazados = [p for p in flujo.pending if p.step_id == dinamico.id]
    assert enlazados and enlazados[0].text.startswith("p.sas:1")


def test_seccion_grande_se_parte_en_tramos_por_dataset_escrito():
    pasos = [_paso(f"a{i}", "uno") for i in range(SECCION_MAX_PASOS)]
    pasos += [_paso("b1", "dos"), _paso("b2", None), _paso("c1", "tres")]
    tramos = _tramos("S", pasos)
    assert [nombre for nombre, _ in tramos] == ["S · uno", "S · dos", "S · tres"]
    assert [len(items) for _, items in tramos] == [SECCION_MAX_PASOS, 2, 1]


def test_seccion_chica_no_se_parte():
    pasos = [_paso("a", "uno"), _paso("b", "dos")]
    assert _tramos("S", pasos) == [("S", pasos)]


def test_vista_por_seccion_cuenta_todos_los_pasos_una_vez():
    flujo = _flujo(PROGRAMA)
    vista = by_section(flujo)
    total = sum(int(m) for n in vista.steps for m in re.findall(r"· (\d+) pasos?", n.type_name))
    assert total == len(flujo.steps)


def test_vista_por_seccion_de_programa_vacio_no_falla():
    vista = by_section(_flujo("%let a = 1;\n"))
    assert vista.steps == []
    ET.fromstring(render_svg(vista))


def test_ninguna_conexion_va_hacia_una_capa_menor():
    for modelo in (_flujo(PROGRAMA), by_section(_flujo(PROGRAMA))):
        capa = {s.id: s.layer for s in modelo.steps}
        capa.update({e.id: 0 for e in modelo.inputs})
        for arista in modelo.edges:
            assert capa[arista.target] > capa[arista.source], arista


def test_cada_nodo_del_svg_tiene_posicion_unica():
    flujo = _flujo(PROGRAMA)
    pos = positions(flujo)
    assert len(set(pos.values())) == len(pos)


class _Equilibrio(HTMLParser):
    """Comprueba que cada etiqueta que se abre se cierra, sin contar las vacías."""

    VACIAS = {"meta", "br", "img", "input", "hr", "link", "path", "rect"}

    def __init__(self) -> None:
        super().__init__()
        self.pila: list[str] = []
        self.errores: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VACIAS:
            self.pila.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in self.VACIAS:
            return
        if not self.pila or self.pila[-1] != tag:
            self.errores.append(f"cierre {tag} inesperado")
            return
        self.pila.pop()


def test_html_tiene_etiquetas_balanceadas():
    parser = _Equilibrio()
    parser.feed(render_page(_flujo(PROGRAMA)))
    assert parser.errores == []
    assert parser.pila == []


def test_golden_de_la_pagina_no_cambia():
    texto = (REPO / "tests" / "fixtures" / "sas" / "p1_merge_first_last.sas").read_text(
        encoding="utf-8", errors="replace"
    )
    html = render_page(_flujo(texto, "p1_merge_first_last.sas"))
    html = FECHA.sub("Generado el FECHA", html)
    assert html == GOLDEN.read_text(encoding="utf-8")


def test_programa_vacio_y_con_bom_se_leen():
    assert _flujo("").steps == []
    flujo = _flujo("﻿data a; set b; run;\n")
    assert [s.title for s in flujo.steps] == ["DATA a"]


def test_comando_crea_la_carpeta_y_escribe_json(tmp_path):
    fuente = tmp_path / "p.sas"
    fuente.write_bytes("data a; set b; run;\n".encode("latin-1"))
    destino = tmp_path / "nueva" / "salida"
    flujo_command(source=fuente, out=destino, como_json=True)
    assert (destino / "p.flujo.html").exists()
    assert json.loads((destino / "p.flujo.json").read_text(encoding="utf-8"))["version"] == 1


def test_carpeta_de_generalizacion_se_analiza_sin_errores():
    carpeta = REPO / "tests" / "fixtures" / "sas" / "generalization"
    archivos = {
        p.name: p.read_text(encoding="utf-8", errors="replace") for p in carpeta.glob("*.sas")
    }
    modelos = build_flows(archivos)
    assert set(modelos) == set(archivos)
    assert any(m.steps for m in modelos.values())


def test_programa_sin_etiquetas_cae_en_una_sola_seccion():
    flujo = _flujo(PROGRAMA)
    assert {s.label for s in flujo.steps} == {None}
    vista = by_section(flujo)
    assert [n.title for n in vista.steps] == ["(sin sección)"]
    assert vista.steps[0].type_name == f"Sección · {len(flujo.steps)} pasos"
    una_linea = _flujo("data a; set b; run;\n")
    assert by_section(una_linea).steps[0].type_name == "Sección · 1 paso"
    # Las únicas aristas salen de la entrada externa; no hay conexiones entre pasos.
    assert all(e.source.startswith("e") for e in vista.edges)


def test_paso_de_proc_muestra_su_dataset_en_vez_de_repetir_el_tipo():
    flujo = _flujo(PROGRAMA)
    sort = next(s for s in flujo.steps if s.id == "p3")
    assert etiqueta_paso(sort) == "→ resumen"
    assert etiqueta_paso(flujo.steps[0]) == "DATA trabajo.clientes"


def test_salidas_finales_son_los_datasets_que_nadie_lee():
    flujo = _flujo("data trabajo.x; set entrada.y; run;\n")
    assert [u.nombre for u in salidas_finales(flujo)] == ["trabajo.x"]
    assert salidas_finales(_flujo(PROGRAMA)) == []


def test_frase_resumen_dice_entradas_pasos_y_salidas():
    flujo = _flujo("data trabajo.x; set entrada.y; run;\n")
    frase = frase_resumen(flujo, ["trabajo.x"])
    assert frase == (
        "Lee 1 entrada externa (entrada.y), ejecuta 1 paso, deja 1 salida final (trabajo.x)."
    )


def test_frase_resumen_de_programa_vacio():
    assert frase_resumen(_flujo("%let a = 1;\n"), []).startswith("El programa no tiene pasos")


def test_dataset_con_macrovariable_se_marca_como_dinamico():
    html = render_page(_flujo("data t; set w.&tabla; run;\n"))
    assert es_dinamico("w.&tabla")
    assert 'class="badge"' in html
    assert not es_dinamico("w.tabla")


def test_etapa_con_muchos_datasets_resume_el_resto():
    texto = "".join(f"data d{i}; set a; run;\n" for i in range(7))
    html = render_page(_flujo(texto))
    assert "y 2 más" in html
