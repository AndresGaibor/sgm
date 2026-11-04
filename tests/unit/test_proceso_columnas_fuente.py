"""Pruebas de `sgm.proceso.columnas_fuente`: reglas con casos sintéticos y un caso real.

Los casos sintéticos usan nombres genéricos. El caso real lee el programa grande del cliente y sus
nombres solo aparecen aquí, en el test, nunca en `src/`.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

from sgm.proceso.columnas_fuente import (
    ImportacionExcel,
    columnas_por_importacion,
    columnas_usadas,
    datasets_importados,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sas" / "client" / "client_large.sas"


# --- datasets_importados -------------------------------------------------------------------


def test_importacion_basica_con_datafile_y_out():
    texto = "PROC IMPORT DATAFILE='C:\\datos\\uno.xlsx' DBMS=EXCELCS OUT=WORK.Uno REPLACE;\nRUN;\n"
    assert datasets_importados(texto) == [ImportacionExcel("C:\\datos\\uno.xlsx", "Uno", 1)]


def test_opciones_en_varias_lineas_y_file_en_lugar_de_datafile():
    texto = (
        "/* etiqueta */\n"
        "proc import\n"
        "  file='/ruta/dos.xlsx'\n"
        "  dbms=excelcs\n"
        "  out=work.Dos\n"
        "  replace;\n"
        "run;\n"
    )
    assert datasets_importados(texto) == [ImportacionExcel("/ruta/dos.xlsx", "Dos", 2)]


def test_ignora_importaciones_sin_datafile_o_sin_out_o_con_otra_biblioteca():
    texto = (
        "PROC IMPORT OUT=WORK.SinRuta DBMS=EXCELCS REPLACE;\nRUN;\n"
        "PROC IMPORT DATAFILE='a.xlsx' DBMS=EXCELCS REPLACE;\nRUN;\n"
        "PROC IMPORT DATAFILE='b.xlsx' OUT=OTRA.Tabla REPLACE;\nRUN;\n"
        "PROC IMPORT DATAFILE='c.xlsx' OUT=WORK.Ok REPLACE;\nRUN;\n"
    )
    assert [i.dataset for i in datasets_importados(texto)] == ["Ok"]


def test_proc_import_dentro_de_comentario_no_cuenta():
    texto = "/* PROC IMPORT DATAFILE='x.xlsx' OUT=WORK.X; RUN; */\nproc sql; quit;\n"
    assert datasets_importados(texto) == []


# --- columnas_usadas: regla 1, alias ------------------------------------------------------


def test_alias_con_as():
    texto = "proc sql;\ncreate table s as select t.A, t.B from WORK.D as t;\nquit;"
    assert columnas_usadas(texto, "D") == ["A", "B"]


def test_alias_sin_as():
    texto = "proc sql; select t1.X from WORK.D t1 where t1.Y = 1; quit;"
    assert columnas_usadas(texto, "D") == ["X", "Y"]


def test_alias_omitido_usa_el_nombre_del_dataset_con_where():
    texto = "proc sql; select D.C from WORK.D where D.K = 2; quit;"
    assert columnas_usadas(texto, "D") == ["C", "K"]


def test_alias_omitido_con_left_join_no_toma_left_como_alias():
    texto = "proc sql; select E.Z from WORK.E E left join WORK.D on (D.K = E.K); quit;"
    assert columnas_usadas(texto, "D") == ["K"]


def test_alias_reutilizado_en_otra_sentencia_no_mezcla_columnas():
    texto = (
        "proc sql; select t1.X from WORK.D t1 where t1.X > 0; quit;\n"
        "proc sql; select t1.Y from WORK.E t1 where t1.Y > 0; quit;\n"
    )
    assert columnas_usadas(texto, "D") == ["X"]
    assert columnas_usadas(texto, "E") == ["Y"]


def test_join_con_dos_tablas_en_la_misma_sentencia_separa_por_alias():
    texto = (
        "proc sql; create table r as select a.P, b.Q from WORK.D a "
        "inner join WORK.E b on (a.K = b.K); quit;"
    )
    # `a` es el alias de D, así que `a.K` en el ON también es columna de D.
    assert columnas_usadas(texto, "D") == ["P", "K"]
    assert columnas_usadas(texto, "E") == ["Q", "K"]


def test_nombre_de_dataset_con_mayusculas_distintas_y_referencia_con_work_minuscula():
    texto = "proc sql; select v.A from work.validacion_FECHA v; quit;"
    assert columnas_usadas(texto, "VALIDACION_fecha") == ["A"]


def test_dataset_con_nombre_parecido_no_coincide():
    texto = "proc sql; select t.A from WORK.D_AHO t; quit;"
    assert columnas_usadas(texto, "D") == []


def test_columna_sin_calificar_no_se_inventa_y_star_no_cuenta():
    texto = "proc sql; select C, * from WORK.D; quit;"
    assert columnas_usadas(texto, "D") == []


def test_asterisco_de_multiplicacion_no_es_comentario():
    texto = "proc sql; select t.A * 2 as B from WORK.D t; quit;"
    assert columnas_usadas(texto, "D") == ["A"]


# --- regla 2: INTO -----------------------------------------------------------------------


def test_select_into_aporta_la_columna():
    texto = "proc sql; SELECT COL INTO :var FROM WORK.D; quit;"
    assert columnas_usadas(texto, "D") == ["COL"]


def test_select_into_sin_espacio_antes_de_los_dos_puntos_y_con_nombre_no_ascii():
    texto = "proc sql;\nSELECT AÑO INTO: ANIO FROM WORK.VALIDACION_FECHA;\nquit;"
    assert columnas_usadas(texto, "VALIDACION_FECHA") == ["AÑO"]


def test_select_into_de_otra_tabla_no_cuenta():
    texto = "proc sql; SELECT COL INTO :var FROM WORK.OTRA; quit;"
    assert columnas_usadas(texto, "D") == []


# --- regla 3: rename ---------------------------------------------------------------------


def test_rename_simple_aporta_el_nombre_viejo():
    texto = "data x; set WORK.D(rename=Viejo=Nuevo); run;"
    assert columnas_usadas(texto, "D") == ["Viejo"]


def test_rename_con_parentesis_y_varios_pares():
    texto = "data x; set WORK.D(rename=(a=b c=d)); run;"
    assert columnas_usadas(texto, "D") == ["a", "c"]


def test_rename_con_otras_opciones_antes_y_despues():
    texto = "data x; set WORK.D(keep=k rename=(a=b) drop=z); run;"
    assert columnas_usadas(texto, "D") == ["a"]


# --- comentarios, orden, unicidad, no ASCII ----------------------------------------------


def test_comentarios_de_bloque_y_de_sentencia_se_ignoran():
    texto = (
        "/* select t.OCULTA from WORK.D t; */\n"
        "* select t.TAMPOCO from WORK.D t;\n"
        "proc sql; select t.VISIBLE from WORK.D t; quit;\n"
    )
    assert columnas_usadas(texto, "D") == ["VISIBLE"]


def test_punto_y_coma_dentro_de_cadena_no_corta_la_sentencia():
    texto = "proc sql; select t.A from WORK.D t where t.B = 'x;y' and t.C = 1; quit;"
    assert columnas_usadas(texto, "D") == ["A", "B", "C"]


def test_sin_repetir_sin_distinguir_mayusculas_y_conserva_la_primera_forma():
    texto = "proc sql; select t.abc, t.ABC, t.Abc from WORK.D t; quit;"
    assert columnas_usadas(texto, "D") == ["abc"]


def test_orden_de_primera_aparicion_entre_reglas():
    texto = (
        "proc sql; SELECT Z INTO :z FROM WORK.D; quit;\n"
        "data x; set WORK.D(rename=Y=W); run;\n"
        "proc sql; select t.X from WORK.D t; quit;\n"
    )
    assert columnas_usadas(texto, "D") == ["Z", "Y", "X"]


def test_columna_con_n_tilde_y_acentos_con_comillas_sas():
    texto = "proc sql; select v.'AÑO'n, v.MÉS from WORK.D v; quit;"
    assert columnas_usadas(texto, "D") == ["AÑO", "MÉS"]


# --- columnas_por_importacion ----------------------------------------------------------------


def test_por_importacion_une_ruta_con_sus_columnas_y_vacia_si_no_hay_uso():
    texto = (
        "PROC IMPORT DATAFILE='a.xlsx' DBMS=EXCELCS OUT=WORK.A REPLACE;\nRUN;\n"
        "PROC IMPORT DATAFILE='b.xlsx' DBMS=EXCELCS OUT=WORK.B REPLACE;\nRUN;\n"
        "proc sql; select t.P from WORK.A t; quit;\n"
    )
    assert columnas_por_importacion(texto) == {"a.xlsx": ["P"], "b.xlsx": []}


# --- caso real: programa grande del cliente ----------------------------------------------


def _normalizar(texto: str) -> str:
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sin_acentos.upper()


def _columnas_del_excel(mapa: dict[str, list[str]], sufijo: str) -> list[str]:
    """Columnas de la única importación cuya ruta termina en `sufijo` (busca por sufijo)."""
    hallados = [
        columnas
        for ruta, columnas in mapa.items()
        if ruta.replace("\\", "/").endswith("/" + sufijo)
    ]
    assert len(hallados) == 1, f"se esperaba una importación que termine en {sufijo}"
    return hallados[0]


def test_programa_real_columnas_de_los_excel_importados():
    texto = FIXTURE.read_text(encoding="utf-8", errors="replace")
    mapa = columnas_por_importacion(texto)

    homologacion = {_normalizar(c) for c in _columnas_del_excel(mapa, "Homologacion_tpo_dto.xlsx")}
    assert "CNAME" in homologacion

    validacion = {_normalizar(c) for c in _columnas_del_excel(mapa, "Validacion_fecha.xlsx")}
    assert {"ANO", "MES"} <= validacion

    pais = {_normalizar(c) for c in _columnas_del_excel(mapa, "Cod_pais.xlsx")}
    assert "CODIGO_PAIS" in pais


def test_programa_real_todas_las_importaciones_excel_tienen_ruta_con_xlsx():
    texto = FIXTURE.read_text(encoding="utf-8", errors="replace")
    excel = [i for i in datasets_importados(texto) if i.ruta.lower().endswith(".xlsx")]
    assert len(excel) == 5
