"""Pruebas directas de `fuentes_csv` y `esquema_csv` sobre un SAS sintético.

El SAS de prueba es ficticio: baja `DBIFTCD.csv` con PROC DOWNLOAD, lo importa con PROC IMPORT
DBMS=DLM (sin cabecera) y usa `VAR1`, `VAR2` y `VAR3`.
"""

from __future__ import annotations

import pytest

from sgm.proceso.esquema_csv import esquema_csv
from sgm.proceso.fuentes_csv import fuentes_csv

PRODUCTOS = {"cte": ("CORRIENTE",)}

IMPORT_SIN_CABECERA = """\
/* Etiqueta: Importar Corriente */
PROC DOWNLOAD INFILE='/ruta/DBIFTCD.csv' OUTFILE='/tmp/tmp1.csv';
RUN;
PROC IMPORT DATAFILE='/tmp/tmp1.csv' OUT=WORK.Base DBMS=DLM REPLACE;
  DELIMITER=';';
  GETNAMES=NO;
RUN;
"""

USO_DE_COLUMNAS = """\
proc sql;
  create table WORK.Salida as
  select DS.VAR1 AS NOMBRE
  from WORK.Base DS;
quit;
DATA WORK.Salida2;
  SET WORK.Base;
  X=input(left(VAR2), 10.);
  Z=VAR3;
RUN;
"""

SAS_SIN_CABECERA = IMPORT_SIN_CABECERA + USO_DE_COLUMNAS


def test_fuentes_csv_describe_el_archivo_sin_cabecera():
    fuentes = fuentes_csv(SAS_SIN_CABECERA, PRODUCTOS)

    assert len(fuentes) == 1
    fuente = fuentes[0]
    assert fuente.ruta_origen == "/ruta/DBIFTCD.csv"
    assert fuente.archivo == "DBIFTCD.csv"
    assert fuente.dataset == "Base"
    assert fuente.delimitador == ";"
    assert fuente.con_cabecera is False
    assert fuente.columnas == 3
    assert fuente.producto == "cte"


@pytest.mark.parametrize(
    "opcion",
    ["  GETNAMES=YES;\n", ""],
    ids=["getnames_yes", "sin_getnames"],
)
def test_import_con_cabecera_queda_pendiente_de_columnas(opcion):
    texto = (
        "/* Etiqueta: Importar Corriente */\n"
        "PROC DOWNLOAD INFILE='/ruta/DBIFTCD.csv' OUTFILE='/tmp/tmp1.csv';\nRUN;\n"
        "PROC IMPORT DATAFILE='/tmp/tmp1.csv' OUT=WORK.Base DBMS=DLM REPLACE;\n"
        "  DELIMITER=';';\n"
        f"{opcion}"
        "RUN;\n"
        "DATA WORK.Salida;\n  SET WORK.Base;\n  X=input(left(VAR2), 10.);\nRUN;\n"
    )

    fuentes = fuentes_csv(texto, PRODUCTOS)

    assert len(fuentes) == 1
    assert fuentes[0].con_cabecera is True
    assert fuentes[0].columnas == 0


def test_proc_import_de_excel_se_ignora():
    texto = (
        "/* Etiqueta: Importar Corriente */\n"
        "PROC IMPORT DATAFILE='/ruta/Corriente.xlsx' OUT=WORK.Hoja DBMS=EXCELCS REPLACE;\n"
        "RUN;\n"
        "proc sql; select H.VAR1 from WORK.Hoja H; quit;\n"
    )

    assert fuentes_csv(texto, PRODUCTOS) == []


def test_esquema_csv_nombra_y_tipa_las_columnas_que_el_sas_demuestra():
    fuente = fuentes_csv(SAS_SIN_CABECERA, PRODUCTOS)[0]

    columnas = esquema_csv(SAS_SIN_CABECERA, fuente)

    assert [c.posicion for c in columnas] == [1, 2, 3]
    nombre, x, z = columnas
    assert (nombre.nombre, nombre.numerica, nombre.demostrada) == ("NOMBRE", False, True)
    assert (x.nombre, x.numerica, x.demostrada) == ("X", True, True)
    assert (z.nombre, z.numerica, z.demostrada) == ("VAR3", False, False)
