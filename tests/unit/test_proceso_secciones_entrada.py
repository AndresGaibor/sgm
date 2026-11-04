"""Tests de las secciones 1.1 y 1.4: declaración, hallazgo en el SAS y pendientes."""

from __future__ import annotations

import pytest

from sgm.flow.model import build_flows
from sgm.proceso.entradas_salidas import entradas_y_salidas
from sgm.proceso.secciones_entrada import cargar_declaradas, seccion_fuentes, seccion_salidas

PROGRAMA = """\
proc import datafile="/in/Lookup.xlsx" out=work.lk dbms=xlsx replace; run;
data work.a; set work.lk; run;
proc export data=work.a outfile="/out/TOTAL_X.csv" dbms=csv replace; run;
proc export data=work.a outfile="/out/TOTAL_Y.csv" dbms=csv replace; run;
"""

YAML = r"""
fuentes:
  - {clave: Lookup, busca: 'lookup\.xlsx$', ubicacion: 'ruta + arch', uso: 'Busca algo'}
  - {clave: Ausente, busca: 'nada\.xlsx$', ubicacion: 'ruta + otro', estado_sin_hallar: 'pend (n)'}
salidas:
  - {clave: totales, creado_en: job_t, contenido: Totales, equivalente_busca: '^TOTAL_'}
  - {clave: ninguna, creado_en: job_t, equivalente_busca: '^NO_EXISTE'}
  - {clave: fija, creado_en: job_t, equivalente_sas: texto declarado}
"""


@pytest.fixture
def es():
    modelo = build_flows({"p.sas": PROGRAMA})["p.sas"]
    return entradas_y_salidas(modelo, {})


@pytest.fixture
def ruta(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text(YAML, encoding="utf-8")
    return p


def test_fuente_hallada_toma_el_tipo_del_sas_y_queda_confirmada(ruta, es):
    fila = seccion_fuentes(cargar_declaradas(ruta, "fuentes"), es)["Lookup"]
    assert fila == {
        "tipo": "Excel",
        "ubicacion": "ruta + arch",
        "uso": "Busca algo",
        "estado": "Ruta confirmada en SAS",
    }


def test_fuente_no_hallada_queda_pendiente_con_el_estado_declarado(ruta, es):
    fila = seccion_fuentes(cargar_declaradas(ruta, "fuentes"), es)["Ausente"]
    assert fila["estado"] == "pend (n)"
    assert fila["tipo"] == "pendiente"


def test_salidas_lista_lo_que_el_sas_escribe_o_dice_que_no(ruta, es):
    seccion = seccion_salidas(cargar_declaradas(ruta, "salidas"), es)
    assert seccion["totales"]["equivalente_sas"] == "TOTAL_X.csv, TOTAL_Y.csv"
    assert seccion["ninguna"]["equivalente_sas"].startswith("pendiente")
    assert seccion["fija"]["equivalente_sas"] == "texto declarado"


@pytest.mark.parametrize(
    "texto, mensaje",
    [
        ("fuentes:\n  - {uso: x}\n", "necesita `clave`"),
        ("fuentes:\n  - {clave: a}\n  - {clave: a}\n", "repite la clave"),
        ("fuentes:\n  - {clave: a, busca: '('}\n", "inválido"),
    ],
)
def test_yaml_mal_formado_falla_con_motivo(tmp_path, texto, mensaje):
    p = tmp_path / "d.yaml"
    p.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError, match=mensaje):
        cargar_declaradas(p, "fuentes")
