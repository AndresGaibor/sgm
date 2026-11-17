"""B-11: `MERGE` con la semántica de SAS en el intérprete. Una fila por iteración, no un producto.

Páginas: `lrcon` p. 593 (uno a uno), p. 600 (muchos a muchos: el valor retenido), p. 601 (llave en un solo lado),
p. 594 (sin BY, por posición), p. 75 (`IN=` vale 1 solo si la entrada aportó en esa observación), p. 584 (los datos
deben estar ordenados por BY); `lestmtsref`, p. 243 (si una columna se repite, gana la última entrada).
"""

from __future__ import annotations

import pytest

from sgm.migrar.interprete_base import NoSoportadoEnInterprete
from sgm.migrar.interprete_filas import _mezclar


def _mezcla(entradas, banderas=None, por=("k",), tipo="full"):
    banderas = banderas or [None] * len(entradas)
    return _mezclar(entradas, banderas, {"by": list(por), "join_type": tipo})


def test_uno_a_uno_da_una_fila_por_pareja():  # lrcon p. 593
    a = [{"k": "1", "a": "x"}, {"k": "2", "a": "y"}]
    b = [{"k": "1", "b": "p"}, {"k": "2", "b": "q"}]
    salida = _mezcla([a, b])
    assert [(f["a"], f["b"]) for f in salida] == [("x", "p"), ("y", "q")]


def test_grupo_de_dos_y_tres_da_tres_filas_y_repite_la_ultima_de_la_corta():  # lrcon p. 600
    a = [{"k": "1", "a": "1"}, {"k": "1", "a": "2"}]
    b = [{"k": "1", "b": "1"}, {"k": "1", "b": "2"}, {"k": "1", "b": "3"}]
    salida = _mezcla([a, b])
    assert [(f["a"], f["b"]) for f in salida] == [("1", "1"), ("2", "2"), ("2", "3")]


def test_llave_en_un_solo_lado_deja_la_otra_entrada_con_faltante_e_in_cero():  # lrcon p. 601
    a = [{"k": "1", "a": "x"}]
    b = [{"k": "2", "b": "q"}]
    salida = _mezcla([a, b], banderas=["ina", "inb"])
    assert [f["k"] for f in salida] == ["1", "2"]
    assert salida[0]["ina"] == 1 and salida[0]["inb"] == 0
    assert salida[1]["ina"] == 0 and salida[1]["inb"] == 1


def test_in_vale_uno_solo_en_las_observaciones_que_la_entrada_aporta():  # lrcon p. 75
    # La entrada B tiene una observación en el grupo: en la segunda iteración ya no aporta.
    a = [{"k": "1", "a": "1"}, {"k": "1", "a": "2"}]
    b = [{"k": "1", "b": "1"}]
    salida = _mezcla([a, b], banderas=["ina", "inb"])
    assert [(f["ina"], f["inb"]) for f in salida] == [(1, 1), (1, 0)]


def test_sin_by_une_por_posicion_y_repite_la_ultima_de_la_corta():  # lrcon p. 594
    a = [{"a": "1"}, {"a": "2"}, {"a": "3"}]
    b = [{"b": "9"}, {"b": "8"}]
    salida = _mezcla([a, b], por=())
    assert [(f["a"], f["b"]) for f in salida] == [("1", "9"), ("2", "8"), ("3", "8")]


def test_entrada_desordenada_se_rechaza_y_no_se_ordena_sola():  # lrcon p. 584
    a = [{"k": "2", "a": "x"}, {"k": "1", "a": "y"}]
    b = [{"k": "1", "b": "p"}]
    with pytest.raises(NoSoportadoEnInterprete, match="p. 584"):
        _mezcla([a, b])


def test_columna_con_el_mismo_nombre_gana_la_ultima_entrada():  # lestmtsref p. 243
    a = [{"k": "1", "v": "a"}]
    b = [{"k": "1", "v": "b"}]
    salida = _mezcla([a, b])
    assert salida[0]["v"] == "b"
