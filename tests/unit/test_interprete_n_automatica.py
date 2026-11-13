"""B-20 (a): `_N_` cuenta las iteraciones del DATA step, no las filas que se escriben (`lrcon`, p. 79 y p. 500).

El contador se calcula en la asignación que va antes de cualquier filtro del paso. Con cuatro filas y un
`IF valor > 0` después, las dos que quedan tienen `_N_` 2 y 4, no 1 y 2.
"""

from __future__ import annotations

from sgm.migrar.interprete_filas import _filtrar, _proyectar


def test_n_cuenta_iteraciones_y_no_filas_escritas():
    filas = [{"valor": "-1"}, {"valor": "3"}, {"valor": "0"}, {"valor": "5"}]
    con_n = _proyectar(filas, [{"target": "n", "expression": "_N_"}], aditivo=True)
    salida = _filtrar(con_n, "valor > 0")
    assert [int(float(f["n"])) for f in salida] == [2, 4]


def test_el_contador_no_se_escribe_como_columna_de_salida():
    # El contador sirve para evaluar `_N_`, pero no es una columna del dataset de salida.
    filas = [{"valor": "1"}]
    salida = _proyectar(filas, [{"target": "n", "expression": "_N_"}], aditivo=True)
    assert set(salida[0].keys()) == {"valor", "n"}
