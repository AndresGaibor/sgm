"""Pruebas del expansor de macros: evaluación parcial, dinámicos, duplicados e includes."""

from sgm.frontend.macros import MacroDynamic
from sgm.frontend.program import analyze_program
from sgm.frontend.steps import DataStep


def _datas(files: dict[str, str]) -> list[DataStep]:
    result = analyze_program(files)
    return [i.item for i in result.items if isinstance(i.item, DataStep)]


def _outputs(files: dict[str, str]) -> list[str]:
    return [name for step in _datas(files) for name in step.outputs]


def test_let_constante_se_sustituye():
    assert _outputs({"p.sas": "%let anio = 2025;\ndata x_&anio; set s; run;"}) == ["x_2025"]


def test_do_con_limites_constantes_se_despliega():
    text = (
        "%macro m;\n%do i = 1 %to 3;\ndata t&i; set s; run;\n%end;\n%mend;\n%m;\n"
    )
    assert _outputs({"p.sas": text}) == ["t1", "t2", "t3"]


def test_do_con_paso_negativo_y_by():
    text = "%macro m;\n%do i = 4 %to 2 %by -1;\ndata u&i; set s; run;\n%end;\n%mend;\n%m;"
    assert _outputs({"p.sas": text}) == ["u4", "u3", "u2"]


def test_if_con_condicion_constante_elige_una_rama():
    text = (
        "%let modo = prod;\n"
        "%if &modo = prod %then %do;\ndata p; set s; run;\n%end;\n"
        "%else %do;\ndata d; set s; run;\n%end;\n"
    )
    assert _outputs({"p.sas": text}) == ["p"]


def test_llamada_con_parametros_posicionales_y_por_nombre():
    text = (
        "%macro t(tabla, anio=2020);\ndata &tabla._&anio; set s; run;\n%mend;\n"
        "%t(x);\n%t(y, anio=2021);\n"
    )
    assert _outputs({"p.sas": text}) == ["x_2020", "y_2021"]


def test_macro_dinamica_se_marca_con_su_texto_y_motivo():
    text = (
        "%let v = %sysfunc(today());\n"
        "data a; set s; call symputx('n', 5); run;\n"
        "%do i = 1 %to &n_desconocido;\ndata b&i; set s; run;\n%end;\n"
    )
    result = analyze_program({"p.sas": text})
    dynamics = [i.item for i in result.items if isinstance(i.item, MacroDynamic)]
    assert len(dynamics) >= 3
    assert all(d.reason == "MACRO_DINAMICA" and d.text for d in dynamics)
    details = " | ".join(d.detail for d in dynamics)
    assert "call symput" in details and "sysfunc" in details and "límites" in details


def test_condicion_no_constante_marca_dinamico_y_no_adivina_la_rama():
    text = "%if &desconocida = 1 %then %do;\ndata a; set s; run;\n%end;\n"
    result = analyze_program({"p.sas": text})
    assert not _outputs({"p.sas": text})
    assert any(isinstance(i.item, MacroDynamic) for i in result.items)


def test_definiciones_identicas_se_indexan_una_vez():
    body = "%macro comun;\ndata c; set s; run;\n%mend;\n"
    result = analyze_program({"a.sas": body, "b.sas": body})
    assert len(result.index) == 1
    assert result.index.duplicates == 1


def test_include_resuelto_expande_la_macro_del_archivo_incluido():
    files = {
        "main.sas": "%include 'inc/m.sas';\n%m;\n",
        "inc/m.sas": "%macro m;\ndata q; set s; run;\n%mend;\n",
    }
    result = analyze_program(files)
    assert [s.outputs for s in _datas(files)] == [["q"]]
    assert result.unresolved_includes == []


def test_include_externo_queda_sin_resolver_con_motivo():
    result = analyze_program({"main.sas": "%include '/no/existe/x.sas';\n"})
    assert result.unresolved_includes == [("main.sas", "/no/existe/x.sas", "external")]


def test_cada_paso_lleva_la_etiqueta_de_su_nodo():
    text = "/* Etiqueta: Carga */\ndata a; set s; run;\n/* Etiqueta: Fin */\ndata b; set a; run;\n"
    labels = [i.label for i in analyze_program({"p.sas": text}).items]
    assert labels == ["Carga", "Fin"]
