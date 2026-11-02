"""Pruebas del hito 10: caché, paralelismo, aislamiento de errores, orden por inclusiones, linaje y métricas."""

import json

from typer.testing import CliRunner

from sgm import batch, diagnostics, lineage, metrics
from sgm.cli import app
from sgm.emit.plan_json import plan_to_dict

PROGRAMA_A = "data lz.t; set s; where x > 1; run;\n"
PROGRAMA_B = "data b; set lz.t; keep x; run;\n"


def test_paralelo_da_el_mismo_plan_que_secuencial():
    files = {"a.sas": PROGRAMA_A, "b.sas": PROGRAMA_B}
    secuencial, _ = batch.compile_batch(files, workers=1)
    paralelo, _ = batch.compile_batch(files, workers=2)
    for name in files:
        assert plan_to_dict(secuencial[name].plan) == plan_to_dict(paralelo[name].plan)


def test_un_archivo_que_falla_no_detiene_a_los_demas(monkeypatch):
    real = batch.compile_file

    def fallar_para_uno(analysis, program, base):
        if program == "malo.sas":
            raise RuntimeError("fallo simulado")
        return real(analysis, program, base)

    monkeypatch.setattr(batch, "compile_file", fallar_para_uno)
    compiled, _ = batch.compile_batch({"malo.sas": PROGRAMA_A, "bueno.sas": PROGRAMA_B}, workers=1)
    assert [g.reason for g in compiled["malo.sas"].plan.gaps] == ["PARSE_ERROR"]
    assert len(compiled["bueno.sas"].plan.graph) > 0


def test_el_archivo_incluido_va_primero():
    files = {
        "a_principal.sas": "%include 'inc/macros.sas';\n%m;\n",
        "inc/macros.sas": "%macro m;\ndata q; set s; run;\n%mend;\n",
    }
    assert batch.include_order(files)[0] == "inc/macros.sas"


def test_linaje_pone_al_consumidor_en_una_oleada_posterior():
    compiled, _ = batch.compile_batch({"a.sas": PROGRAMA_A, "b.sas": PROGRAMA_B}, workers=1)
    assert lineage.waves(compiled) == [["a.sas"], ["b.sas"]]


def test_linaje_ignora_work_que_es_local_a_cada_programa():
    compiled, _ = batch.compile_batch(
        {"a.sas": "data w; set s; run;\n", "b.sas": "data w; set s; run;\n"}, workers=1
    )
    assert lineage.waves(compiled) == [["a.sas", "b.sas"]]


def test_metricas_por_programa_y_total(tmp_path):
    files = {"a.sas": "/* Etiqueta: Carga */\n" + PROGRAMA_A, "b.sas": PROGRAMA_B}
    compiled, analysis = batch.compile_batch(files, workers=1)
    report = metrics.compute(compiled, files, analysis)
    assert report["total"]["programas"] == 2
    assert report["programas"]["a.sas"]["nodos_sas"] == 1
    assert 0 <= report["total"]["pct_tjava"] <= 100
    assert set(report["programas"]["a.sas"]) >= {"componentes", "jobs", "subjobs", "pct_tjava"}


def test_metricas_y_diagnostico_cuentan_candidatas_talend():
    files = {
        "mas_candidatas.sas": (
            "data a; set s; z = scan(x, 2); q = scan(y, 1); run;"
        ),
        "una_candidata.sas": "data b; set s; z = strip(scan(x, 2)); run;",
        "informato_numerico.sas": "data c; set s; z = input(x, 8.); run;",
    }
    compiled, analysis = batch.compile_batch(files, workers=1)

    report = metrics.compute(compiled, files, analysis)
    program = report["programas"]["mas_candidatas.sas"]

    assert program["expresiones_talend_candidatas"] == 2
    assert program["operadores_con_expresiones_talend"] == 1
    assert program["funciones_sas_candidatas"] == {"scan": 2}
    assert report["total"]["expresiones_talend_candidatas"] == 4
    assert report["total"]["operadores_con_expresiones_talend"] == 3
    assert report["total"]["funciones_sas_candidatas"] == {
        "input": 1,
        "scan": 3,
        "strip": 1,
    }
    assert report["total"]["advertencias_en_candidatas_talend"] == {
        "input numérico: el valor se convierte con Mathematical.REAL; comprobar el informato": 1,
        "scan: los delimitadores consecutivos cuentan como uno, como en SAS": 3,
    }
    diagnosis = diagnostics.render(diagnostics.build(compiled), report)
    assert "Candidatas Talend pendientes de validar en Studio: 4 en 3 operadores" in diagnosis
    assert "| mas_candidatas.sas | 2 | 1 |" in diagnosis
    assert diagnosis.index("mas_candidatas.sas") < diagnosis.index("una_candidata.sas")
    assert "| scan | 3 |" in diagnosis
    assert "| strip | 1 |" in diagnosis
    assert "| scan: los delimitadores consecutivos cuentan como uno, como en SAS | 3 |" in diagnosis
    assert "| input numérico: el valor se convierte con Mathematical.REAL; comprobar el informato | 1 |" in diagnosis


def test_cli_compile_usa_la_cache_y_se_invalida_al_cambiar_un_archivo(tmp_path, monkeypatch):
    monkeypatch.setenv("SGM_DB", str(tmp_path / "cache.sqlite"))
    fuente = tmp_path / "src"
    fuente.mkdir()
    (fuente / "a.sas").write_text(PROGRAMA_A, encoding="utf-8")
    salida = tmp_path / "out"
    runner = CliRunner()
    primera = runner.invoke(app, ["compile", str(fuente), "--out", str(salida)])
    assert primera.exit_code == 0, primera.output
    segunda = runner.invoke(app, ["compile", str(fuente), "--out", str(salida)])
    assert "Caché" in segunda.output
    (fuente / "a.sas").write_text(PROGRAMA_A + "data c; set s; run;\n", encoding="utf-8")
    tercera = runner.invoke(app, ["compile", str(fuente), "--out", str(salida)])
    assert "Caché" not in tercera.output and tercera.exit_code == 0


def test_cli_metrics_escribe_metrics_json(tmp_path, monkeypatch):
    monkeypatch.setenv("SGM_DB", str(tmp_path / "m.sqlite"))
    fuente = tmp_path / "src"
    fuente.mkdir()
    (fuente / "a.sas").write_text(PROGRAMA_A, encoding="utf-8")
    salida = tmp_path / "out"
    resultado = CliRunner().invoke(app, ["metrics", str(fuente), "--out", str(salida)])
    assert resultado.exit_code == 0, resultado.output
    datos = json.loads((salida / "metrics.json").read_text(encoding="utf-8"))
    assert "total" in datos and "programas" in datos and "top_huecos" in datos


def test_cli_lineage_imprime_oleadas(tmp_path):
    fuente = tmp_path / "src"
    fuente.mkdir()
    (fuente / "a.sas").write_text(PROGRAMA_A, encoding="utf-8")
    (fuente / "b.sas").write_text(PROGRAMA_B, encoding="utf-8")
    resultado = CliRunner().invoke(app, ["lineage", str(fuente)])
    assert (
        resultado.exit_code == 0
        and "Oleada 1" in resultado.output
        and "Oleada 2" in resultado.output
    )
