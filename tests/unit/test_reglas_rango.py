"""Pruebas de las reglas de rango del SAS (T14)."""

from pathlib import Path

import pytest

from sgm.proceso.reglas import reglas

GRANDE = Path(__file__).resolve().parents[1] / "fixtures" / "sas" / "client" / "client_large.sas"

SINTETICO = """
proc sql;
create table work.rechazos as
select t1.TIPO_CTA
from work.sabana t1
where
   (
      ( t1.TIPO_CTA NOT BETWEEN 1 AND 5 ) AND
      ( t1.RELACION = 1000 )
   );
quit;
data work.temporal;
set WORK.rechazos;
INCONSISTENCIA='TIPO CTA INVALIDO';
run;
"""

VALIDOS = """
proc sql;
create table work.validos as
select t1.TIPO_CTA
from work.sabana t1
where ( t1.TIPO_CTA BETWEEN 1 AND 5 );
quit;
"""


def test_detecta_el_rango_negado_con_su_control_y_su_motivo():
    (regla,) = reglas(SINTETICO)

    assert (regla.columna, regla.desde, regla.hasta) == ("TIPO_CTA", 1, 5)
    assert regla.permite is False
    assert regla.control == ("RELACION", "1000")
    assert regla.motivo == "TIPO CTA INVALIDO"
    assert regla.destino == "rechazos"


def test_la_condicion_agrupa_el_rango_negado_antes_del_control():
    (regla,) = reglas(SINTETICO)

    assert regla.condicion == (
        "(fila.TIPO_CTA < 1 || fila.TIPO_CTA > 5) && fila.RELACION == 1000"
    )


def test_un_between_sin_not_es_la_lista_de_validos():
    (regla,) = reglas(VALIDOS)

    assert regla.permite is True
    assert regla.control is None
    assert regla.motivo == ""
    assert regla.condicion == "fila.TIPO_CTA >= 1 && fila.TIPO_CTA <= 5"


@pytest.fixture(scope="module")
def sas_grande() -> str:
    return GRANDE.read_text(encoding="latin-1")


def test_el_programa_grande_declara_tipo_de_cuenta_y_codex(sas_grande):
    encontradas = {(r.columna.upper(), r.desde, r.hasta, r.permite, r.motivo) for r in reglas(sas_grande)}

    assert ("TIPO_CTA", 1, 5, False, "TIPO CTA INVALIDO") in encontradas
    assert ("GMF", 1, 10, False, "CODEX INVALIDO") in encontradas
    assert ("TIPO_CTA", 1, 5, False, "TIPO DE CUENTA INVALIDO") in encontradas
    assert ("GMF", 1, 10, False, "GMF INVALIDO") in encontradas


def test_cada_producto_tiene_su_par_de_validos_y_rechazos(sas_grande):
    cuenta = [r for r in reglas(sas_grande) if r.columna.upper() == "TIPO_CTA" and (r.desde, r.hasta) == (1, 5)]

    assert any(r.permite for r in cuenta)
    assert any(not r.permite for r in cuenta)
    assert all(r.control in (None, ("RELACION", "1000")) for r in cuenta)
