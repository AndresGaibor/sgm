"""Hito 91 / R1-05: la regla de ubicación se lee del caso v03, no se inventa.

Las variantes se hacen cambiando una sola cosa del programa de v03, para que cada prueba falle por
una causa concreta. El programa de cliente no tiene la forma del caso y debe fallar.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas_ubicacion import reglas_ubicacion

RAIZ = Path(__file__).resolve().parents[2]
V03 = RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v03_pais_dane" / "programa.sas"
CLIENTE = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
TEXTO_V03 = V03.read_text(encoding="utf-8", errors="replace")


def _cambiar(texto: str, viejo: str, nuevo: str) -> str:
    """Sustituye un fragmento que debe aparecer exactamente una vez."""
    assert texto.count(viejo) == 1, f"el fragmento no es único: {viejo!r}"
    return texto.replace(viejo, nuevo)


def test_lee_los_productos_y_los_motivos_del_caso():
    regla = reglas_ubicacion(TEXTO_V03)
    assert regla.productos == ("AHO", "CTE")
    assert regla.motivo_pais == "PAIS NO HOMOLOGADO"
    assert regla.motivo_dane == "DANE NO HOMOLOGADO"
    assert regla.motivo_extranjera == "UBICACION EXTRANJERA CON CODIGO"
    assert regla.motivo_direccion == "DIRECCION INVALIDA"


def test_lee_el_literal_de_pais_longitud_y_fragmento():
    regla = reglas_ubicacion(TEXTO_V03)
    assert regla.literal_pais == "900"
    assert regla.longitud_minima == 8
    assert regla.fragmento == "sin dir"


def test_lee_los_excel_de_homologacion_y_sus_columnas():
    regla = reglas_ubicacion(TEXTO_V03)
    assert regla.archivo_pais == "Cod_pais.xlsx"
    assert regla.columna_pais == "Codigo_Pais"
    assert regla.archivo_dane == "CODIGOS_DANE.xlsx"
    assert regla.columna_dane == "CODIGO_DANE"


def test_la_proyeccion_del_rechazo_termina_en_inconsistencia():
    regla = reglas_ubicacion(TEXTO_V03)
    assert regla.proyeccion_rechazo == (
        "LLAVE_NOMBRE", "RELACION", "TIPO_DOC", "NRO_DOC", "PAIS", "CODIGO_UBICACION",
        "DIRECCION", "INCONSISTENCIA",
    )  # fmt: skip
    assert regla.proyeccion_valida == regla.proyeccion_rechazo[:-1]
    assert regla.llave == "LLAVE_NOMBRE"


def test_publica_los_pendientes_de_codigo_pais_caso_y_union():
    regla = reglas_ubicacion(TEXTO_V03)
    unidos = " | ".join(regla.pendientes)
    assert "input()" in unidos
    assert "CASE" in unidos
    assert "SABANA_UBIC" in unidos


def test_el_programa_de_cliente_no_tiene_la_forma_del_caso():
    texto = CLIENTE.read_text(encoding="utf-8", errors="replace")
    with pytest.raises(ValueError):
        reglas_ubicacion(texto)


def test_falta_la_tabla_de_rechazo():
    # La macro crea INCONS_UBICACION_<P>; sin ese nombre no hay rechazo que leer.
    texto = _cambiar(
        TEXTO_V03, "CREATE TABLE WORK.INCONS_UBICACION_&sufijo", "CREATE TABLE WORK.X_&sufijo"
    )
    with pytest.raises(ValueError):
        reglas_ubicacion(texto)


def test_falta_la_alternativa_de_longitud_del_where():
    texto = _cambiar(TEXTO_V03, "OR LENGTH(t1.DIRECCION) < 8\n   OR", "OR")
    with pytest.raises(ValueError):
        reglas_ubicacion(texto)


def test_el_umbral_de_longitud_se_lee_del_sas_y_no_se_fija():
    # El lector no fija 8: lo que diga el SAS es la regla. Un 9 en el programa da un 9.
    texto = _cambiar(TEXTO_V03, "LENGTH(t1.DIRECCION) < 8", "LENGTH(t1.DIRECCION) < 9")
    assert reglas_ubicacion(texto).longitud_minima == 9


def test_el_motivo_del_case_se_lee_del_sas_y_no_se_fija():
    texto = _cambiar(TEXTO_V03, "THEN 'DANE NO HOMOLOGADO'", "THEN 'DANE INVALIDO'")
    assert reglas_ubicacion(texto).motivo_dane == "DANE INVALIDO"


def test_cambia_el_orden_de_las_ramas_del_case():
    viejo = (
        "WHEN t3.Codigo_Pais IS MISSING THEN 'PAIS NO HOMOLOGADO'\n"
        "   WHEN t1.PAIS = '900' AND t2.CODIGO_DANE IS MISSING THEN 'DANE NO HOMOLOGADO'"
    )
    nuevo = (
        "WHEN t1.PAIS = '900' AND t2.CODIGO_DANE IS MISSING THEN 'DANE NO HOMOLOGADO'\n"
        "   WHEN t3.Codigo_Pais IS MISSING THEN 'PAIS NO HOMOLOGADO'"
    )
    with pytest.raises(ValueError):
        reglas_ubicacion(_cambiar(TEXTO_V03, viejo, nuevo))


def test_falta_el_else_de_direccion():
    texto = _cambiar(TEXTO_V03, "ELSE 'DIRECCION INVALIDA'", "")
    with pytest.raises(ValueError):
        reglas_ubicacion(texto)


def test_quita_el_left_join_de_dane():
    texto = _cambiar(
        TEXTO_V03,
        "LEFT JOIN WORK.FORMATO_CODIGO_DANE t2\nON ( t1.CODIGO_UBICACION = t2.CODIGO_DANE )",
        "",
    )
    with pytest.raises(ValueError):
        reglas_ubicacion(texto)


def test_el_literal_de_extranjera_debe_ser_el_mismo_que_el_de_dane():
    # Solo la alternativa del WHERE cambia; la rama del CASE sigue con '900'.
    texto = _cambiar(TEXTO_V03, "OR ( t1.PAIS <> '900'", "OR ( t1.PAIS <> '901'")
    with pytest.raises(ValueError):
        reglas_ubicacion(texto)


def test_el_not_in_de_validos_debe_cruzar_la_tabla_de_rechazo():
    texto = _cambiar(
        TEXTO_V03, "FROM WORK.INCONS_UBICACION_&sufijo t4", "FROM WORK.UBIC_VALIDA_&sufijo t4"
    )
    with pytest.raises(ValueError):
        reglas_ubicacion(texto)

