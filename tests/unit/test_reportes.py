"""Reportes impresos (R6): PROC PRINT, PROC REPORT y PROC CONTENTS según `reports` del proyecto."""

from pathlib import Path

from sgm.catalog.config import Env, Project, load_env
from sgm.compile import compile_project

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "tests" / "fixtures" / "sas" / "client"
PROGRAMA = "proc print data=work.x; run;\nproc contents data=work.y; run;\n"


def _env(policy: str) -> Env:
    return Env(project=Project(reports=policy))


def _plan(program: str, policy: str):
    compiled, _ = compile_project({"p.sas": program}, env=_env(policy))
    return compiled["p.sas"].plan


def test_discard_no_migra_el_reporte_y_no_es_hueco():
    plan = _plan(PROGRAMA, "discard")
    assert not [g for g in plan.gaps if g.reason == "PROC_NO_SOPORTADO"]
    assert any("PROC PRINT" in nm.what for nm in plan.not_migrated)
    assert not any(op.params.get("procedure") == "print" for op in plan.graph.operators())


def test_la_politica_por_defecto_descarta_reportes():
    plan = _plan("proc print data=work.x; run;\n", Project().reports)
    assert Project().reports == "discard"
    assert any("PROC PRINT" in nm.what for nm in plan.not_migrated)


def test_tabulate_con_discard_es_reporte_explicito_y_no_hueco_generico():
    plan = _plan("proc tabulate data=work.x; var amount; table amount; run;\n", "discard")
    assert not [g for g in plan.gaps if g.reason == "PROC_NO_SOPORTADO"]
    assert any("PROC TABULATE" in nm.what for nm in plan.not_migrated)


def test_reportes_no_print_no_se_convierten_en_filas_crudas():
    for policy in ("log", "csv"):
        for procedure in ("report", "tabulate", "contents"):
            plan = _plan(f"proc {procedure} data=work.x; run;\n", policy)
            assert any(g.reason == "REPORTE" for g in plan.gaps), (policy, procedure)
            assert not any(op.kind in {"report", "write_file"} for op in plan.graph.operators()), (
                policy,
                procedure,
            )


def test_log_usa_tlogrow():
    plan = _plan(PROGRAMA, "log")
    components = [op.component["name"] for op in plan.graph.operators() if op.component]
    assert "tLogRow" in components


def test_csv_escribe_a_fichero_con_la_ruta_como_contexto():
    plan = _plan(PROGRAMA, "csv")
    outputs = [op for op in plan.graph.operators() if op.kind == "write_file"]
    assert any(op.params.get("outfile") == "contexto.ruta_print" for op in outputs)
    assert all(op.params.get("dbms") == "csv" for op in outputs)
    names = [op.component["name"] for op in outputs if op.component]
    assert "tFileOutputDelimited" in names


def test_proc_contents_con_out_sigue_siendo_hueco():
    """`out=` crea un dataset que otros pasos leen: no es un reporte."""
    plan = _plan("proc contents data=work.y out=contenido; run;\n", "discard")
    assert any(g.reason == "PROC_NO_SOPORTADO" for g in plan.gaps)


def test_con_discard_desaparecen_proc_print_y_proc_contents_del_cliente():
    compiled, _ = compile_project(
        {
            "client_poc.sas": (CLIENT / "client_poc.sas").read_text(
                encoding="utf-8", errors="replace"
            )
        },
        env=load_env(ROOT / "env"),
    )
    gaps = compiled["client_poc.sas"].plan.gaps
    texts = [g.text.lower() for g in gaps]
    assert not any(t.startswith("proc print") or t.startswith("proc contents") for t in texts)


def test_discard_reemplaza_el_cierre_ods_por_fontaneria():
    plan = _plan("ods html close;\nods rtf (id=web) close;\n", "discard")
    assert not [g for g in plan.gaps if g.reason == "SENTENCIA_NO_SOPORTADA"]
    assert any("ODS" in item.what for item in plan.not_migrated)


def test_log_conserva_cierre_ods_como_pendiente():
    plan = _plan("ods html close;\n", "log")
    assert any(g.reason == "SENTENCIA_NO_SOPORTADA" for g in plan.gaps)
