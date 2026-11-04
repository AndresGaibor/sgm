"""Origen de datos de los productos: archivos delimitados, columnas y esquema deducidos del SAS."""

from __future__ import annotations

from pathlib import Path

from sgm.agrupacion import cargar_declaracion
from sgm.proceso.origen_producto import origenes_producto

RAIZ = Path(__file__).resolve().parents[2]


def test_cada_producto_tiene_su_archivo_principal_de_23_columnas_con_nombres_del_sas():
    texto = (RAIZ / "tests/fixtures/sas/client/client_large.sas").read_text(
        encoding="utf-8", errors="replace"
    )
    productos = cargar_declaracion(RAIZ / "decisiones" / "client_large.agrupacion.yaml").productos
    o = origenes_producto(texto, productos)
    assert {p: x.fuente.archivo for p, x in o.por_producto.items()} == {
        "cte": "DBIFTCD.csv",
        "aho": "DBIFTCS.csv",
        "nequi": "F_1019.csv",
    }
    assert len(o.columnas_comunes) == 23
    assert {"NRO_CTA", "TIPO_DOC", "FIN_SALDO_CTA"} <= set(o.columnas_comunes)
    assert any("Base_datos_Nequi.csv" in p and "auxiliar" in p for p in o.pendientes)


def test_un_csv_con_cabecera_deja_las_columnas_pendientes():
    sas = (
        "/* Etiqueta: Importar Corriente */\n"
        "PROC DOWNLOAD INFILE='/o/A.csv' OUTFILE='/t/A.csv'; run;\n"
        "proc import datafile='/t/A.csv' out=WORK.A dbms=dlm replace; delimiter=','; run;\n"
    )
    o = origenes_producto(sas, {"cte": ("CORRIENTE",)})
    assert o.por_producto["cte"].columnas == ()
    assert o.por_producto["cte"].fuente.con_cabecera is True
