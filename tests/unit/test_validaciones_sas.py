"""Pruebas del detector del patrón de validación por lookup (T11)."""

from pathlib import Path

import pytest

from sgm.proceso.validaciones import ruta_de_dataset, validaciones

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sas"
GRANDE = FIXTURES / "client" / "client_large.sas"

IMPORT = """
proc import datafile='C:/datos/Homologacion_tpo_dto.xlsx' dbms=excelcs
    out=WORK.IMPORT_HOMOLOGACION_TPO_DOC replace;
run;
"""


def _programa(cuerpo: str, importacion: str = IMPORT) -> str:
    return importacion + "\nproc sql;\n" + cuerpo + "\nquit;\n"


SIN_PARENTESIS = """create table work.rechazos as
select s.tipo_doc
from work.sabana s
left join work.import_homologacion_tpo_doc h
on s.tipo_doc = h.cname
where h.cname is missing;"""

CON_PARENTESIS_Y_AS = """create table work.rechazos as
select s.tipo_doc
from work.sabana s
left join work.import_homologacion_tpo_doc as cat
on ( s.tipo_doc = cat.cname )
where cat.cname is null;"""

INNER = """create table work.validos as
select s.tipo_doc
from work.sabana s
inner join work.import_homologacion_tpo_doc cat
on ( cat.cname = s.tipo_doc );"""


def test_detecta_el_patron_sin_parentesis():
    (validacion,) = validaciones(_programa(SIN_PARENTESIS))

    assert validacion.columna == "tipo_doc"
    assert validacion.columna_lookup == "cname"
    assert validacion.fuente_lookup == "work.import_homologacion_tpo_doc"
    assert validacion.dataset == "import_homologacion_tpo_doc"
    assert validacion.linea > 5
    assert validacion.linea_valida is None


def test_detecta_el_patron_con_paréntesis_alias_con_as_e_is_null():
    (validacion,) = validaciones(_programa(CON_PARENTESIS_Y_AS))

    assert (validacion.columna, validacion.columna_lookup) == ("tipo_doc", "cname")


def test_la_pareja_inner_join_queda_enlazada_y_admite_el_on_invertido():
    texto = _programa(SIN_PARENTESIS + "\n" + INNER)

    (validacion,) = validaciones(texto)
    assert validacion.linea_valida is not None
    assert validacion.linea_valida > validacion.linea


def test_un_lookup_que_no_viene_de_proc_import_no_es_una_validacion():
    cuerpo = SIN_PARENTESIS.replace("work.import_homologacion_tpo_doc", "work.otro_dataset")

    assert validaciones(_programa(cuerpo)) == []


def test_un_left_join_sin_filtro_de_faltante_no_es_una_validacion():
    cuerpo = SIN_PARENTESIS.replace("where h.cname is missing", "")

    assert validaciones(_programa(cuerpo)) == []


def test_un_where_que_filtra_otra_columna_no_es_una_validacion():
    cuerpo = SIN_PARENTESIS.replace("where h.cname is missing", "where h.otra is missing")

    assert validaciones(_programa(cuerpo)) == []


def test_lee_el_nombre_literal_de_sas_como_columna():
    cuerpo = SIN_PARENTESIS.replace("h.cname", "h.'codigo dian'n")

    (validacion,) = validaciones(_programa(cuerpo))
    assert validacion.columna_lookup == "codigo dian"


@pytest.fixture(scope="module")
def sas_grande() -> str:
    return GRANDE.read_text(encoding="latin-1")


def test_el_programa_grande_detecta_las_dos_validaciones_de_tipo_de_documento(sas_grande):
    encontradas = validaciones(sas_grande)

    documentos = [v for v in encontradas if v.columna.upper() == "TIPO_DOC"]
    assert len(documentos) == 2
    assert all(v.columna_lookup.upper() == "CNAME" for v in documentos)
    assert all(v.dataset.upper() == "IMPORT_HOMOLOGACION_TPO_DOC" for v in documentos)
    assert all(v.linea_valida is not None for v in documentos)


def test_la_ruta_del_catalogo_sale_del_proc_import(sas_grande):
    ruta = ruta_de_dataset(sas_grande, "WORK.IMPORT_HOMOLOGACION_TPO_DOC")
    nequi = ruta_de_dataset(sas_grande, "Homologacion_tpo_dto_Nequi")

    assert ruta is not None and ruta.endswith("Homologacion_tpo_dto.xlsx")
    assert nequi is not None and nequi.endswith("Homologacion_tpo_dto_Nequi.xlsx")
    assert ruta_de_dataset(sas_grande, "WORK.NO_EXISTE") is None


def test_cada_producto_empareja_su_propio_inner_join(sas_grande):
    documentos = [v for v in validaciones(sas_grande) if v.columna.upper() == "TIPO_DOC"]

    assert {v.sabana.upper() for v in documentos} == {
        "SABANA_SIN_PAQ_VACIO_0_AHO",
        "SABANA_SIN_PAQ_VACIO_0_CTE",
    }
    assert all(v.linea_valida is not None for v in documentos)
    assert len({v.linea_valida for v in documentos}) == 2


def test_detecta_las_validaciones_de_ubicacion(sas_grande):
    encontradas = {
        (v.columna.upper(), v.columna_lookup.upper(), v.dataset.upper())
        for v in validaciones(sas_grande)
    }

    assert ("CODIGO_UBICACION", "CODIGO_DANE", "IMPORT_CODIGOS_DANE") in encontradas
    assert ("PAIS", "CODIGO_PAIS", "IMPORT_CODIGOS_PAIS") in encontradas
