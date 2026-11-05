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


def test_los_informats_reales_del_sas_llegan_a_las_columnas_comunes():
    texto = (RAIZ / "tests/fixtures/sas/client/client_large.sas").read_text(
        encoding="utf-8", errors="replace"
    )
    productos = cargar_declaracion(RAIZ / "decisiones" / "client_large.agrupacion.yaml").productos

    numericas = origenes_producto(texto, productos).numericas_comunes

    assert len(numericas) == 15
    assert numericas["NRO_CTA"] == (30, 0)
    assert numericas["TIPO_DOC"] == (8, 0)
    assert numericas["GMF"] == (3, 0)
    assert numericas["FIN_SALDO_CTA"] == (30, 0)
    assert "ANIO_PROCESO" not in numericas  # solo alias, el SAS no la convierte con input()
    assert set(numericas) <= set(origenes_producto(texto, productos).columnas_comunes)


def _sas_con_dos_productos(informat_cte: str, informat_aho: str) -> str:
    """Dos importaciones sin cabecera, cada una con su propia conversión de VAR1."""
    return (
        "/* Etiqueta: Importar Corriente */\n"
        "PROC DOWNLOAD INFILE='/o/CTE.csv' OUTFILE='/t/cte.csv'; run;\n"
        "PROC IMPORT DATAFILE='/t/cte.csv' OUT=WORK.Cte DBMS=DLM REPLACE;\n"
        " DELIMITER=';'; GETNAMES=NO; RUN;\n"
        "DATA WORK.Cte2; SET WORK.Cte;\n"
        f" X=input(left(VAR1), {informat_cte});\nRUN;\n"
        "/* Etiqueta: Importar Ahorro */\n"
        "PROC DOWNLOAD INFILE='/o/AHO.csv' OUTFILE='/t/aho.csv'; run;\n"
        "PROC IMPORT DATAFILE='/t/aho.csv' OUT=WORK.Aho DBMS=DLM REPLACE;\n"
        " DELIMITER=';'; GETNAMES=NO; RUN;\n"
        "DATA WORK.Aho2; SET WORK.Aho;\n"
        f" X=input(left(VAR1), {informat_aho});\nRUN;\n"
    )


def test_un_mismo_informat_en_dos_productos_no_deja_pendiente():
    texto = _sas_con_dos_productos("30.", "30.")
    o = origenes_producto(texto, {"cte": ("CORRIENTE",), "aho": ("AHORRO",)})

    assert o.numericas_comunes == {"X": (30, 0)}
    assert not any("informats distintos" in p for p in o.pendientes)


def test_informats_distintos_quedan_pendientes_en_lugar_de_elegirse_en_silencio():
    texto = _sas_con_dos_productos("8.", "30.")
    o = origenes_producto(texto, {"cte": ("CORRIENTE",), "aho": ("AHORRO",)})

    assert o.numericas_comunes == {"X": (8, 0)}
    assert any(
        "X: los productos declaran informats distintos [(8, 0), (30, 0)]" in p
        for p in o.pendientes
    )
