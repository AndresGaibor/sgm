"""Tests de las familias de regiones: normalización, producto, agrupación y diferencias."""

from __future__ import annotations

from sgm.proceso.familias import (
    detectar_familias,
    diferencias,
    normalizar_region,
    producto_de_texto,
    similitud,
)

SUFIJOS = ["CTE", "AHO", "NEQUI"]
PRODUCTOS = {"cte": ("CTE",), "aho": ("AHO",), "nequi": ("NEQUI",)}


def _region(sufijo: str, extra: str = "") -> str:
    return (
        f"/* Etiqueta: carga {sufijo} */\n"
        f"data work.base_{sufijo}; set lz.origen_{sufijo};  run;\n"
        f"proc sort data=work.base_{sufijo}; by id; run;\n"
        f"proc sql; create table work.final_{sufijo} as select * from work.base_{sufijo}; quit;\n"
        f"{extra}"
    )


def test_normalizacion_quita_comentarios_espacios_y_sufijo():
    lineas = normalizar_region(_region("CTE"), SUFIJOS)
    assert lineas[0] == "data work.base_{P}; set lz.origen_{P}; run;"
    assert all("etiqueta" not in linea for linea in lineas)


def test_normalizacion_sin_sufijos_solo_limpia():
    assert normalizar_region("A   B\n\n C", []) == ["a b", "c"]


def test_el_sufijo_solo_cuenta_al_final_de_una_palabra_con_guion_bajo():
    lineas = normalizar_region("data a_CTEX; set CTE; set b_cte_1;", SUFIJOS)
    assert lineas == ["data a_ctex; set cte; set b_{P}_1;"]


def test_producto_dominante_empate_y_ausencia():
    assert producto_de_texto(_region("AHO"), PRODUCTOS) == "aho"
    assert producto_de_texto("data x_CTE; set y_AHO;", PRODUCTOS) is None  # empate
    assert producto_de_texto("data x; run;", PRODUCTOS) is None


def test_similitud_de_regiones_que_solo_cambian_el_sufijo_es_uno():
    a = normalizar_region(_region("CTE"), SUFIJOS)
    b = normalizar_region(_region("NEQUI"), SUFIJOS)
    assert similitud(a, b) == 1.0


def test_similitud_descarta_por_tamano_sin_comparar():
    assert similitud(["a"] * 100, ["a"], minimo=0.9) == 0.0


def test_tres_productos_forman_una_familia_y_la_otra_region_queda_unica():
    textos = {
        0: _region("CTE"),
        1: _region("AHO", "data work.solo_aho; run;\n"),
        2: _region("NEQUI"),
        3: "proc print data=otra; run;\nproc means data=otra2; run;\n",
    }
    lineas = {r: normalizar_region(t, SUFIJOS) for r, t in textos.items()}
    productos = {r: producto_de_texto(t, PRODUCTOS) for r, t in textos.items()}
    resultado = detectar_familias(lineas, productos, umbral=0.8)
    assert resultado.unicas == (3,)
    (familia,) = resultado.familias
    assert [(i.region, i.producto) for i in familia.instancias] == [
        (0, "cte"),
        (1, "aho"),
        (2, "nequi"),
    ]
    assert 0.8 <= familia.similitud_minima < 1.0
    assert familia.productos_repetidos == ()


def test_dos_regiones_del_mismo_producto_se_senalan_como_repetidas():
    textos = {0: _region("CTE"), 1: _region("CTE"), 2: _region("AHO")}
    lineas = {r: normalizar_region(t, SUFIJOS) for r, t in textos.items()}
    productos = {r: producto_de_texto(t, PRODUCTOS) for r, t in textos.items()}
    (familia,) = detectar_familias(lineas, productos).familias
    assert familia.productos_repetidos == ("cte",)


def test_diferencias_listan_solo_lo_que_cambia_fuera_del_sufijo():
    a = normalizar_region(_region("CTE"), SUFIJOS)
    b = normalizar_region(_region("AHO", "where x = 1;\n"), SUFIJOS)
    assert diferencias(a, b) == [([], ["where x = 1;"])]
