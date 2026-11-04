"""Resolución de insumos de archivo: ruta, variables de contexto y columnas demostradas."""

from __future__ import annotations

from pathlib import Path

from sgm.proceso.entradas_salidas import nombre_archivo
from sgm.proceso.insumos import resolver_insumos
from sgm.proceso.secciones_entrada import cargar_declaradas

SAS = r"""
PROC IMPORT DATAFILE='\srv\carpeta\Paises.xlsx' DBMS=EXCELCS OUT=WORK.IMP_PAISES REPLACE; RUN;
PROC IMPORT DATAFILE='\srv\carpeta\Sin_uso.xlsx' DBMS=EXCELCS OUT=WORK.IMP_SIN_USO REPLACE; RUN;
PROC SQL;
 CREATE TABLE WORK.X AS SELECT t.A, p.CODIGO FROM WORK.BASE t
 LEFT JOIN WORK.IMP_PAISES p ON (t.PAIS = p.CODIGO);
QUIT;
"""
DECLARADAS = [
    {"clave": "Países", "busca": r"Paises\.xlsx$", "ubicacion": "ruta_insumos + arch_paises"},
    {"clave": "Sin uso", "busca": r"Sin_uso\.xlsx$", "ubicacion": "ruta_insumos + arch_sin_uso"},
    {"clave": "Ausente", "busca": r"Ausente\.xlsx$", "ubicacion": "ruta_insumos + arch_ausente"},
    {"clave": "Mala", "busca": r"x", "ubicacion": "sin formato"},
]


def test_resuelve_ruta_variables_y_columnas_usadas():
    r = resolver_insumos(SAS, DECLARADAS, ["Países"])
    (paises,) = r.insumos.values()
    assert paises.archivo == "Paises.xlsx"
    assert paises.directorio == "\\srv\\carpeta\\"
    assert (paises.variable_ruta, paises.variable_archivo) == ("ruta_insumos", "arch_paises")
    assert paises.columnas == ("CODIGO",)
    assert r.pendientes == []


def test_lo_que_no_se_demuestra_queda_pendiente_con_su_motivo():
    r = resolver_insumos(SAS, DECLARADAS, ["Sin uso", "Ausente", "Mala", "No declarada"])
    motivos = "\n".join(r.pendientes)
    assert "no usa ninguna columna" in motivos
    assert "no importa ningún archivo" in motivos
    assert "no es `variable + variable`" in motivos
    assert "no está declarada" in motivos
    assert r.insumos["Sin uso"].columnas == ()


def test_el_programa_grande_resuelve_las_cinco_fuentes_de_excel():
    raiz = Path(__file__).resolve().parents[2]
    texto = (raiz / "tests/fixtures/sas/client/client_large.sas").read_text(
        encoding="utf-8", errors="replace"
    )
    declaradas = cargar_declaradas(raiz / "decisiones" / "client_large.diseno.yaml", "fuentes")
    claves = [d["clave"] for d in declaradas if d.get("busca")]
    r = resolver_insumos(texto, declaradas, claves)
    assert len(r.insumos) == 5
    assert {nombre_archivo(i.ruta) for i in r.insumos.values()} >= {"Cod_pais.xlsx"}
    assert all(i.columnas for i in r.insumos.values())
    assert r.pendientes == []
