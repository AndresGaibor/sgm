"""El `tMap` lee los nombres como SAS (sin distinguir mayúsculas) y admite el orden ya guardado.

Tres casos que dejaban `l1_09`, `l1_14`, `l2_04` y `l2_05` con pendiente o con una excepción:

* `ON t.tipo_doc = h.CNAME` con la cabecera `CNAME`: el traductor baja los nombres a minúsculas y el
  `tMap` buscaba `cname` en un lookup que tiene `CNAME`.
* `fecha BETWEEN '2026-03-01' AND '2026-03-31'`: el traductor ya escribe el faltante en la
  comparación; envolverla otra vez no hace falta, solo comprobar que la columna sea de texto.
* `cantidad BETWEEN 2 AND 5`: comparar por orden con un número demuestra que la columna es numérica.
"""

from __future__ import annotations

from sgm.expressions.expressions import translate
from sgm.migrar.esquemas import _columnas_ordenadas
from sgm.talend_item.desde_plan_expresiones import cubrir_faltante, expresion, resolver_filas


def test_la_columna_se_resuelve_sin_distinguir_mayusculas():
    java, motivo = resolver_filas("(input_row.cname == null)", {"row1": {"tipo"}, "row2": {"CNAME"}})

    assert motivo is None
    assert java == "(row2.CNAME == null)"


def test_dos_entradas_con_el_mismo_nombre_en_otra_caja_siguen_siendo_ambiguas():
    java, motivo = resolver_filas("input_row.id", {"row1": {"ID"}, "row2": {"id"}})

    assert java is None
    assert "varias entradas" in (motivo or "")


def test_el_orden_de_texto_contra_un_literal_queda_como_lo_escribio_el_traductor():
    sas = "fecha BETWEEN '2026-03-01' AND '2026-03-31'"

    java, motivo = expresion(sas, {"row1": {"fecha"}}, {"row1.fecha": "id_String"})

    assert motivo is None
    assert java is not None
    assert "row1.fecha" in java and "compareTo" in java


def test_el_orden_de_texto_sobre_una_columna_numerica_no_se_admite():
    java = translate("fecha >= '2026-03-01'").talend
    assert java is not None
    resuelta, _ = resolver_filas(java, {"row1": {"fecha"}})

    traducida, motivo = cubrir_faltante(resuelta or "", {"row1.fecha": "id_Double"})

    assert traducida is None
    assert "no lo demuestra" in (motivo or "")


def test_el_orden_numerico_guardado_exige_columna_numerica():
    java = translate("cantidad BETWEEN 2 AND 5").talend
    assert java is not None
    resuelta, _ = resolver_filas(java, {"row1": {"cantidad"}})

    bien, _ = cubrir_faltante(resuelta or "", {"row1.cantidad": "id_Double"})
    mal, motivo = cubrir_faltante(resuelta or "", {"row1.cantidad": "id_String"})

    assert bien == resuelta
    assert mal is None
    assert "numérica" in (motivo or "")


def test_comparar_por_orden_con_un_numero_demuestra_una_columna_numerica():
    assert _columnas_ordenadas("cantidad BETWEEN 2 AND 5") == {"cantidad"}
    assert _columnas_ordenadas("ventas.monto >= 500") == {"monto"}
    assert _columnas_ordenadas("100 > saldo") == {"saldo"}


def test_un_orden_contra_texto_no_demuestra_nada_numerico():
    assert _columnas_ordenadas("fecha >= '2026-03-01'") == set()
    assert _columnas_ordenadas("canal = 'WEB'") == set()
