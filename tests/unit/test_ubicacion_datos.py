"""Hito 91 / R1-05: los datos de la prueba de ubicación se comprueban sin Studio.

Dos cosas independientes del Job: que la clasificación a mano de los vectores coincide con un
segundo cálculo de la regla en Python, y que ese cálculo reproduce el esperado del caso v03 fila por
fila. Así un fallo en Studio no puede deberse a un esperado mal escrito.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))

import ubicacion_datos as datos  # noqa: E402


def test_los_vectores_a_mano_coinciden_con_el_oraculo_python():
    for llave, pais, codigo, direccion, motivo in datos.VECTORES:
        assert datos.clasificar_sas(pais, codigo, direccion) == motivo, llave


def test_hay_veinte_vectores_catorce_rechazos_y_seis_validos():
    motivos = [v[4] for v in datos.VECTORES]
    assert len(motivos) == 20
    assert sum(1 for m in motivos if m) == 14
    assert sum(1 for m in motivos if not m) == 6


def test_los_vectores_cubren_los_bordes_pedidos():
    casos = {v[0]: v for v in datos.VECTORES}
    assert casos["VEC03"][1] == "900 "  # blanco final en el país
    assert casos["VEC06"][2] == "99002  "  # blancos finales en el código
    assert casos["VEC08"][2] == ""  # extranjero sin código
    assert casos["VEC09"][2] == "   "  # código solo con blancos
    assert casos["VEC11"][3] == "ABCDEFGH"  # longitud 8 exacta
    assert casos["VEC12"][3] == "ABCDEFG   "  # 7 caracteres más blancos finales
    assert casos["VEC13"][3] == ""  # dirección vacía
    assert casos["VEC14"][3] == "Sin Dir Nueva 45"  # mayúsculas y minúsculas
    assert casos["VEC15"][3] == "SIN  DIR 45 NORTE"  # dos blancos: no contiene 'SIN DIR'


def test_la_clasificacion_de_sas_trata_el_blanco_final_y_la_longitud_como_sas():
    assert datos.clasificar_sas("900 ", "99001", "CALLE VALIDA 1 2 3") == ""
    assert datos.clasificar_sas("900", "99002  ", "CALLE VALIDA 1 2 3") == ""
    assert datos.clasificar_sas("900", "99003", "ABCDEFG   ") == "DIRECCION INVALIDA"
    assert datos.clasificar_sas("900", "99003", "") == "DIRECCION INVALIDA"


@pytest.mark.parametrize("producto", datos.PRODUCTOS)
def test_el_oraculo_reproduce_el_esperado_del_caso_fila_por_fila(producto, tmp_path):
    """Cada fila de la sábana del caso tiene el motivo que el esperado le asigna."""
    unido, _ = datos.unir(
        datos.ENTRADAS / f"DETALLE_{producto}.csv",
        datos.ENTRADAS / f"UBICACION_{producto}.csv",
        tmp_path / "unido.csv",
    )
    esperados = {
        f[0]: f[-1] for f in datos.esperado(producto, "rechazo", ("LLAVE_NOMBRE", "INCONSISTENCIA"))
    }
    filas = [linea.split(";") for linea in unido.read_text(encoding="utf-8").splitlines()]
    assert len(filas) == len(datos.esperado(producto, "sabana", ("LLAVE_NOMBRE",)))
    for fila in filas:
        motivo = datos.clasificar_sas(fila[23], fila[24], fila[25])
        assert motivo == esperados.get(fila[7], ""), fila[7]


def test_la_union_por_llave_deja_vacia_la_ubicacion_sin_pareja(tmp_path):
    detalle = tmp_path / "d.csv"
    ubic = tmp_path / "u.csv"
    detalle.write_text("a;b;c;d;e;f;g;LLV1\nx;y;z;w;v;u;t;LLV2\n", encoding="utf-8")
    ubic.write_text("LLV1;900;99001;CALLE 1\n", encoding="utf-8")
    destino, sin_pareja = datos.unir(detalle, ubic, tmp_path / "o.csv")
    assert sin_pareja == 1
    filas = destino.read_text(encoding="utf-8").splitlines()
    assert filas[0].endswith(";900;99001;CALLE 1")
    assert filas[1].endswith(";;;")


def test_una_llave_de_ubicacion_repetida_falla(tmp_path):
    detalle = tmp_path / "d.csv"
    ubic = tmp_path / "u.csv"
    detalle.write_text("a;b;c;d;e;f;g;LLV1\n", encoding="utf-8")
    ubic.write_text("LLV1;900;99001;A\nLLV1;902;;B\n", encoding="utf-8")
    with pytest.raises(ValueError):
        datos.unir(detalle, ubic, tmp_path / "o.csv")


def test_el_csv_de_vectores_tiene_veintiseis_campos_por_fila(tmp_path):
    destino = datos.vector_csv(tmp_path / "v.csv")
    filas = [linea.split(";") for linea in destino.read_text(encoding="utf-8").splitlines()]
    assert len(filas) == 20
    assert {len(f) for f in filas} == {26}
    assert filas[0][7] == "VEC01"
    assert filas[0][23:] == ["777", "", "CALLE VALIDA 1 2 3"]
