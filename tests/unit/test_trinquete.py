"""Trinquete de métricas (F1.0): ninguna métrica puede empeorar frente a la línea base."""

from sgm import trinquete

BASE = {
    "total": {
        "pasos_por_componente": 5.0,
        "pct_tjava": 10.0,
        "tjava_sql": 0,
        "subjobs": 100,
        "lineas_sin_cubrir": 4,
        "excepciones": 0,
        "firmas_de_decision": 50,
        "huecos_por_motivo": {"PARSE_ERROR": 2},
        "tiempo_compilacion_s": 100.0,
    }
}


def _now(**changes) -> dict:
    total = dict(BASE["total"], **changes)
    return {"total": total}


def test_sin_cambios_no_hay_violaciones():
    assert trinquete.check(_now(), BASE) == []


def test_pasos_por_componente_no_puede_bajar():
    problems = trinquete.check(_now(pasos_por_componente=4.0), BASE)
    assert any("pasos_por_componente" in p for p in problems)


def test_subjobs_no_puede_subir():
    assert any("subjobs" in p for p in trinquete.check(_now(subjobs=101), BASE))


def test_tjava_sql_no_puede_aparecer():
    assert any("tjava_sql" in p for p in trinquete.check(_now(tjava_sql=1), BASE))


def test_un_motivo_nuevo_cuenta_como_empeoramiento():
    problems = trinquete.check(
        _now(huecos_por_motivo={"PARSE_ERROR": 2, "PROC_NO_SOPORTADO": 1}), BASE
    )
    assert any("PROC_NO_SOPORTADO" in p for p in problems)


def test_el_tiempo_tiene_margen_del_veinte_por_ciento():
    assert trinquete.check(_now(tiempo_compilacion_s=119.0), BASE) == []
    assert any("tiempo" in p for p in trinquete.check(_now(tiempo_compilacion_s=121.0), BASE))


def test_code_lines_ignora_vacias_comentarios_y_bloques_de_comentario():
    text = "/* cabecera\n  sigue aquí */\n\n* comentario SAS;\ndata a; set b; run;\n/* una */ %let x = 1;\n"
    assert trinquete.code_lines(text) == {5, 6}


def test_una_linea_sin_evidencia_cuenta_como_sin_cubrir():
    from sgm.compile import compile_project

    text = "data a; set b; x = 1; run;\n%let w = 2;\n"
    compiled, _ = compile_project({"p.sas": text})
    assert trinquete.uncovered_lines(compiled, {"p.sas": text}) == 0


def test_la_comparacion_exige_el_mismo_corpus():
    baseline = {"total": dict(BASE["total"], programas=189)}
    problems = trinquete.check({"total": dict(BASE["total"], programas=2)}, baseline)
    assert problems and "programas" in problems[0]
