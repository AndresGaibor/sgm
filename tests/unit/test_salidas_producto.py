"""Pruebas de las tablas finales, las exportaciones y la conciliacion del SAS (T19)."""

from pathlib import Path

import pytest

from sgm.proceso.salidas import (
    exportaciones,
    formula_conciliacion,
    tablas_finales,
)

GRANDE = Path(__file__).resolve().parents[1] / "fixtures" / "sas" / "client" / "client_large.sas"

SINTETICO = """
proc sql;
CREATE TABLE work.SABANA_FINAL_PRUEBA AS
SELECT t1.RELACION, t1.TIPO_DOC, t1.'CODIGO DIAN'n
FROM WORK.ALGO t1
ORDER BY 1 ASC;
QUIT;

PROC SQL;
CREATE TABLE WORK.RESULTADO_PRUEBA_NAL AS
SELECT t1.RELACION, t1.PAIS
FROM WORK.SABANA_PRUEBA t1
INNER JOIN WORK.SABANA_TIT_NAL_PRUEBA SABANA_TIT_NAL_PRUEBA
ON ( t1.NRO_CTA = SABANA_TIT_NAL_PRUEBA.NRO_CTA );
QUIT;

proc export data=WORK.RESULTADO_PRUEBA_NAL outfile="/tmp/pcfiles/RESULTADO_PRUEBA_NAL.csv"
dbms=dlm replace;
delimiter=';';
run;

data work.conciliacion;
CONCILIACION_SALDOS=SUMA_SALDO_INICIAL-(SUMA_SALDO_FINAL_DEP_AHO+SUMA_SALDO_INCONS_DEP_AHO);
run;
"""


def test_extrae_las_tablas_finales_con_el_orden_del_select():
    tablas = {tabla.tabla: tabla for tabla in tablas_finales(SINTETICO)}

    assert tablas["SABANA_FINAL_PRUEBA"].columnas == ("RELACION", "TIPO_DOC", "CODIGO DIAN")
    assert tablas["SABANA_FINAL_PRUEBA"].producto == "PRUEBA"
    assert tablas["SABANA_FINAL_PRUEBA"].linea > 1
    assert tablas["RESULTADO_PRUEBA_NAL"].fuente == "SABANA_TIT_NAL_PRUEBA"


def test_una_tabla_con_select_asterisco_no_supone_columnas():
    texto = """
proc sql;
CREATE TABLE WORK.INCONS_DEP_PRUEBA AS
SELECT * FROM WORK.UNO t1
OUTER UNION CORR
SELECT * FROM WORK.DOS t2;
QUIT;
"""

    (tabla,) = tablas_finales(texto)
    assert tabla.columnas == ()


def test_extrae_las_exportaciones_con_su_archivo_y_delimitador():
    (exportacion,) = exportaciones(SINTETICO)

    assert exportacion.dataset == "RESULTADO_PRUEBA_NAL"
    assert exportacion.nombre == "RESULTADO_PRUEBA_NAL.csv"
    assert exportacion.delimitador == ";"
    assert exportacion.reemplaza is True
    assert exportacion.linea > 1


def test_la_formula_de_conciliacion_sale_sin_espacios():
    assert formula_conciliacion(SINTETICO) == (
        "SUMA_SALDO_INICIAL-(SUMA_SALDO_FINAL_DEP_AHO+SUMA_SALDO_INCONS_DEP_AHO)"
    )
    assert formula_conciliacion("proc sql; quit;") is None


@pytest.fixture(scope="module")
def sas_grande() -> str:
    return GRANDE.read_text(encoding="latin-1")


def test_el_programa_grande_declara_la_sabana_final_de_ahorros(sas_grande):
    tablas = {tabla.tabla.upper(): tabla for tabla in tablas_finales(sas_grande)}

    final = tablas["SABANA_FINAL_AHORROS"]
    assert final.producto == "AHORROS"
    assert len(final.columnas) == 19
    assert final.columnas[0] == "RELACION"
    assert final.columnas[-1] == "FIN_SALDO_CTA"
    assert "INCONSISTENCIA" not in final.columnas


def test_nacional_se_arma_con_los_titulares_nacionales_y_extranjero_con_los_extranjeros(sas_grande):
    tablas = {tabla.tabla.upper(): tabla for tabla in tablas_finales(sas_grande)}

    nacional = tablas["RESULTADO_AHO_NAL"]
    extranjero = tablas["RESULTADO_AHO_EXT"]
    assert nacional.fuente.upper() == "SABANA_TIT_NAL_AHO"
    assert extranjero.fuente.upper() == "SABANA_TIT_EXT_AHO"
    assert len(nacional.columnas) == 28
    assert nacional.columnas[0] == "RELACION"
    assert nacional.columnas[-1] == "PROM_DEB_MES"


def test_el_programa_grande_exporta_las_salidas_con_punto_y_coma(sas_grande):
    salidas = exportaciones(sas_grande)
    nombres = {salida.nombre for salida in salidas}

    assert len(salidas) == 22
    assert {"RESULTADO_AHO_NAL.csv", "RESULTADO_AHO_EXT.csv", "INCONS_DEP_AHORROS.csv"} <= nombres
    assert all(salida.delimitador == ";" for salida in salidas)
    assert all(salida.reemplaza for salida in salidas)


def test_el_programa_grande_calcula_la_conciliacion_de_saldos(sas_grande):
    assert formula_conciliacion(sas_grande) == (
        "SUMA_SALDO_INICIAL-(SUMA_SALDO_FINAL_DEP_AHO+SUMA_SALDO_INCONS_DEP_AHO)"
    )
