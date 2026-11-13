"""B-13: qué formas de LAG/DIF se emiten como `tJavaRow` y cuáles siguen como hueco (lefunctionsref, p. 1164).

Solo se emite la forma verificada en `test_java_lag.py`. Cualquier otra devuelve None y el operador queda
como hueco `P-LAG-SIN-EMISOR` (decisión 5: el Job no se escribe).
"""

from __future__ import annotations

from types import SimpleNamespace

from sgm.talend_item.desde_plan_lag import nodo_lag
from sgm.talend_item.modelo import Columna

COLUMNAS = [Columna("id", "id_Integer"), Columna("x", "id_Double"), Columna("t", "id_String")]


def _op(expresion: str, destino: str = "prev", condicion: str | None = None):
    return SimpleNamespace(params={"expression": expresion, "target": destino, "condition": condicion})


def test_lag_numerico_sale_como_tjavarow_con_la_columna_nueva():  # lefunctionsref, p. 1164
    resultado = nodo_lag(_op("LAG(x)"), COLUMNAS, "tJavaRow_1", 0, None, None)
    assert resultado is not None and resultado.nodo.componente == "tJavaRow"
    assert [c.nombre for c in resultado.columnas] == ["id", "x", "t", "prev"]


def test_if_con_condicion_numerica_se_emite():  # lefunctionsref, p. 1164 (trampa de l6_40)
    resultado = nodo_lag(_op("LAG(x)", condicion="x > 0"), COLUMNAS, "tJavaRow_1", 0, None, None)
    assert resultado is not None


def test_dif_se_emite():  # lefunctionsref, p. 663
    assert nodo_lag(_op("DIF2(x)"), COLUMNAS, "tJavaRow_1", 0, None, None) is not None


def test_formas_no_verificadas_quedan_como_hueco():
    assert nodo_lag(_op("LAG(t)"), COLUMNAS, "tJavaRow_1", 0, None, None) is None  # texto
    assert nodo_lag(_op("LAG(x) + 1"), COLUMNAS, "tJavaRow_1", 0, None, None) is None  # compuesta
    assert nodo_lag(_op("LAG(x)", condicion="x > y"), COLUMNAS, "tJavaRow_1", 0, None, None) is None
    assert nodo_lag(_op("LAG(x)", destino="x"), COLUMNAS, "tJavaRow_1", 0, None, None) is None
