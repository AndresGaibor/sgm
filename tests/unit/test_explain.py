"""`sgm explain` (F1.8): una línea muestra su operador, su hueco o que no tiene nada."""

import pytest

from sgm.explain import explicar

PROGRAMA = """\
/* cabecera */
data salida;
  set entrada;
  x = 1;
run;

proc transpose data=a out=b;
  by x;
  id y;
  var z;
run;

proc sql;
  connect to impala (user=u password='claveSECRETA');
quit;
"""


@pytest.fixture
def programa(tmp_path):
    ruta = tmp_path / "programa.sas"
    ruta.write_text(PROGRAMA, encoding="utf-8")
    return ruta


def test_una_linea_de_datos_muestra_su_operador(programa):
    texto = explicar(programa, 2)
    assert texto.startswith("programa.sas:2")
    assert "operador" in texto and "->" in texto


def test_un_proc_sin_soporte_muestra_hueco_dueño_y_arreglo(programa):
    texto = explicar(programa, 7)
    assert "hueco PROC_NO_SOPORTADO" in texto
    assert "dueño joseph" in texto
    assert "se cierra con: rules/sas/procs/" in texto


def test_un_comentario_dice_que_no_tiene_nada(programa):
    assert "ningún operador, hueco ni nota" in explicar(programa, 1)


def test_la_salida_no_muestra_la_credencial(programa):
    assert "claveSECRETA" not in explicar(programa, 14)


def test_linea_fuera_de_rango_falla(programa):
    with pytest.raises(ValueError, match="no existe"):
        explicar(programa, 999)
