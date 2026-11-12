"""Tipos propagados por el plan lógico con su fuente (B-3, MG-P1-02, parte 2)."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.esquemas_propagacion import propagar_tipos


def _plan(texto: str):
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def test_length_declara_caracter_con_largo_y_fuente_declarado() -> None:
    resultado = propagar_tipos(_plan("data work.t; length x $8; x='a'; run;"))
    columna = resultado.tablas["work.t"]["x"]
    assert (columna.tipo, columna.largo, columna.fuente) == ("caracter", 8, "declarado")


def test_aritmetica_da_numerico_y_la_entrada_desconocida_queda_pendiente() -> None:
    resultado = propagar_tipos(_plan("data work.t; y = x + 1; run;"))
    assert resultado.tablas["work.t"]["y"].tipo == "numerico"
    pendientes = [p for p in resultado.pendientes if p.codigo == "P-TIPO-DESCONOCIDO"]
    assert any("x" in p.mensaje for p in pendientes)


def test_set_con_tipos_distintos_es_conflicto_con_ambos_origenes() -> None:
    resultado = propagar_tipos(
        _plan(
            "data work.a; k=1; run; data work.b; k='x'; run;"
            " data work.u; set work.a work.b; run;"
        )
    )
    conflictos = [p for p in resultado.pendientes if p.codigo == "P-UNION-TIPO-CONFLICTO"]
    assert len(conflictos) == 1
    assert "k" in conflictos[0].mensaje
    assert "work.a" in conflictos[0].mensaje and "work.b" in conflictos[0].mensaje


def test_count_en_sql_da_numerico() -> None:
    resultado = propagar_tipos(
        _plan("proc sql; create table work.t as select count(*) as n from work.a; quit;")
    )
    assert resultado.tablas["work.t"]["n"].tipo == "numerico"
