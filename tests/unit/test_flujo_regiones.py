"""Tests de las regiones del flujo: división por marcador, etiquetas y asignación de pasos."""

from __future__ import annotations

from sgm.flow.model import FlowStep, build_flows
from sgm.flow.regiones import asignar_regiones, dividir_regiones, region_de_paso

# La macro `carga` se define en la región 0 (líneas 1-3) y se llama desde la región 1 (línea 10)
# y desde la región 2 (línea 13). Sus dos pasos tienen la misma línea de evidencia (2).
PROGRAMA = """\
%macro carga;
data origen_x; set entrada; run;
%mend carga;
%macro ambiente;
%mend;
data uno; set origen_x; run;
%macro ambiente;
%mend;
/* Etiqueta: Cuentas */
%carga;
%macro ambiente;
%mend;
%carga;
"""


def _flow(texto: str, nombre: str = "p.sas"):
    return build_flows({nombre: texto})[nombre]


def test_varias_regiones_empiezan_en_cada_marcador_excepto_el_primero():
    regiones = dividir_regiones(PROGRAMA, "%macro ambiente")
    assert [(r.indice, r.linea_inicio, r.linea_fin) for r in regiones] == [
        (0, 1, 6),
        (1, 7, 10),
        (2, 11, 13),
    ]


def test_marcador_sin_mayusculas_y_con_espacios_de_mas():
    texto = PROGRAMA.replace("%macro ambiente;", "   %MACRO  AMBIENTE;")
    regiones = dividir_regiones(texto, "%macro ambiente")
    assert [r.linea_inicio for r in regiones] == [1, 7, 11]


def test_marcador_no_casa_con_un_nombre_que_solo_empieza_igual():
    texto = "%macro ambiente_cte;\ndata a; run;\n%macro ambiente;\nrun;\n"
    regiones = dividir_regiones(texto, "%macro ambiente")
    assert [r.linea_inicio for r in regiones] == [1]


def test_sin_marcador_hay_una_sola_region():
    regiones = dividir_regiones("data a; run;\nproc print; run;\n", "%macro ambiente")
    assert len(regiones) == 1
    assert (regiones[0].linea_inicio, regiones[0].linea_fin) == (1, 2)


def test_etiquetas_van_a_su_region_en_orden():
    texto = (
        "/* Etiqueta: Primera */\n"
        "%macro ambiente;\n"
        "/* Etiqueta:   Segunda\n   en dos líneas */\n"
        "%mend;\n"
        "%macro ambiente;\n"
        "/* ETIQUETA: Tercera */\n"
    )
    regiones = dividir_regiones(texto, "%macro ambiente")
    assert regiones[0].etiquetas == ["Primera", "Segunda en dos líneas"]
    assert regiones[1].etiquetas == ["Tercera"]


def test_paso_de_macro_llamada_en_la_region_2_queda_en_la_2():
    flujo = _flow(PROGRAMA)
    regiones = dividir_regiones(PROGRAMA, "%macro ambiente")
    # El cuerpo de `carga` (línea 2) está en la región 0; las llamadas están en 1 y 2.
    expandidos = [s for s in flujo.steps if s.macro_call]
    assert [s.line for s in expandidos] == [2, 2]
    asignacion = asignar_regiones(flujo, regiones)
    assert [asignacion[s.id] for s in expandidos] == [1, 2]


def test_paso_sin_llamada_usa_su_linea():
    flujo = _flow(PROGRAMA)
    regiones = dividir_regiones(PROGRAMA, "%macro ambiente")
    sin_llamada = [s for s in flujo.steps if not s.macro_call]
    assert [s.line for s in sin_llamada] == [6]
    assert asignar_regiones(flujo, regiones)[sin_llamada[0].id] == 0


def test_region_de_paso_lee_la_linea_de_la_clave_de_llamada():
    regiones = dividir_regiones(PROGRAMA, "%macro ambiente")
    paso = FlowStep(
        id="p9",
        file="p.sas",
        line=2,
        label=None,
        kind="data",
        type_name="DATA step",
        title="DATA origen_x",
        macro_call="13:carga",
    )
    assert region_de_paso(paso, regiones) == 2
    paso.macro_call = None
    assert region_de_paso(paso, regiones) == 0


# Una macro externa (definida en la región 0) llama a otra interna (también de la región 0). La
# llamada externa está en la región 1: el paso debe quedar ahí y no en la región 0 donde vive la
# llamada interna.
PROGRAMA_ANIDADO = """\
%macro interna;
data salida_x; set entrada; run;
%mend interna;
%macro externa;
%interna;
%mend externa;
%macro ambiente;
%mend;
data uno; set otra; run;
%macro ambiente;
%mend;
%externa;
"""


def test_paso_de_macro_anidada_queda_en_la_region_de_la_llamada_externa():
    modelo = _flow(PROGRAMA_ANIDADO)
    regiones = dividir_regiones(PROGRAMA_ANIDADO, "%macro ambiente")
    paso = next(p for p in modelo.steps if "salida_x" in p.writes)
    assert paso.outer_call is not None
    assert region_de_paso(paso, regiones) == 1
    # con la llamada interna (línea 5, región 0) el paso quedaría mal asignado
    paso.outer_call = None
    assert region_de_paso(paso, regiones) == 0
