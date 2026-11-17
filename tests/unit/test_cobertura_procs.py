"""Inventario de procedimientos y política de salida, sin equivalencias supuestas."""

import importlib
import re
from pathlib import Path

import pytest
import yaml

from sgm.catalog.config import Env, Project
from sgm.cli_migrar import migrar
from sgm.compile import compile_project

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs/referencia/sas/proc.INDEX.md"
CATALOG = ROOT / "rules/sas/catalogo/procs-usados.yaml"
RULES = ROOT / "rules/sas/procs"


def _tool(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools"))
    assert (ROOT / "tools/cobertura_procs.py").exists(), "falta el generador de C-22"
    return importlib.import_module("cobertura_procs")


def _minimal(tmp_path, names):
    index = tmp_path / "proc.INDEX.md"
    index.write_text(
        "\n".join(f"  - {name} Procedure (p. {page})" for name, page in names), encoding="utf-8"
    )
    catalog = tmp_path / "procs-usados.yaml"
    catalog.write_text("entries: []\n", encoding="utf-8")
    rules = tmp_path / "procs"
    rules.mkdir()
    return index, catalog, rules


def test_indice_minimo_y_familia_desconocida(tmp_path, monkeypatch):
    paths = _minimal(tmp_path, [("PRINT", 1809), ("SORT", 2449), ("CALENDAR", 263), ("NUEVO", 999)])
    rows = {r["procedimiento"]: r for r in _tool(monkeypatch).clasificar(*paths)}
    assert rows["PRINT"]["estado"] == "reporte"
    assert rows["SORT"]["estado"] == "traducido"
    assert rows["CALENDAR"]["estado"] == "fuera_de_alcance"
    assert rows["CALENDAR"]["pagina"] == 263
    assert rows["CALENDAR"]["motivo"]
    assert rows["NUEVO"]["estado"] == "no_verificado"


def test_regla_nueva_y_regla_vacia_no_inventan_soporte(tmp_path, monkeypatch):
    paths = _minimal(tmp_path, [("NUEVO", 900), ("VACIO", 901)])
    for name, ops in [("nuevo", [{"kind": "sort", "params": {}}]), ("vacio", [])]:
        (paths[2] / f"{name}.yaml").write_text(
            yaml.safe_dump(
                {
                    "kind": "proc",
                    "proc": name,
                    "status": "parcial",
                    "ops": ops,
                    "fallback": {"note": "Pendiente: P-NUEVO-SIN-SOPORTE; falta equivalencia"},
                }
            ),
            encoding="utf-8",
        )
    rows = {r["procedimiento"]: r for r in _tool(monkeypatch).clasificar(*paths)}
    assert rows["NUEVO"]["estado"] == "traducido"
    assert rows["VACIO"]["estado"] == "pendiente"
    assert "P-NUEVO-SIN-SOPORTE" in rows["VACIO"]["motivo"]


def test_todos_los_capitulos_y_fuera_de_alcance_con_pagina(monkeypatch):
    rows = _tool(monkeypatch).clasificar(INDEX, CATALOG, RULES)
    chapters = dict(
        re.findall(
            r"^  - ([A-Z][A-Z0-9_]*) Procedure \(p\. (\d+)\)",
            INDEX.read_text(encoding="utf-8"),
            re.M,
        )
    )
    indexed = [r for r in rows if r["capitulo"]]
    assert {r["procedimiento"] for r in indexed} == set(chapters)
    assert len(indexed) == len(chapters)
    for row in rows:
        assert row["estado"] in {
            "traducido",
            "reporte",
            "limpieza",
            "pendiente",
            "fuera_de_alcance",
            "no_verificado",
        }
        if row["estado"] == "fuera_de_alcance":
            assert row["motivo"]
            assert chapters[row["procedimiento"]] == str(row["pagina"])
    freq = next(r for r in rows if r["procedimiento"] == "FREQ")
    assert not freq["capitulo"]
    assert "P-FREQ-OUT-SIN-PAGINA" in freq["motivo"]
    transpose = next(r for r in rows if r["procedimiento"] == "TRANSPOSE")
    assert transpose["estado"] == "pendiente"
    assert "P-OPERADOR-PIVOTAR" in transpose["motivo"]
    format_row = next(r for r in rows if r["procedimiento"] == "FORMAT")
    assert format_row["estado"] == "traducido"
    assert "P-FORMATO-USUARIO-SIN-EMISOR" in format_row["motivo"]


def test_documento_generado_esta_al_dia(tmp_path, monkeypatch):
    tool = _tool(monkeypatch)
    target = tmp_path / "cobertura-procedimientos.md"
    tool.escribir(target, tool.clasificar(INDEX, CATALOG, RULES))
    assert target.read_text(encoding="utf-8") == (
        ROOT / "docs/cobertura-procedimientos.md"
    ).read_text(encoding="utf-8")


def _plan(text, policy="discard"):
    compiled, _ = compile_project({"p.sas": text}, env=Env(project=Project(reports=policy)))
    return compiled["p.sas"].plan


@pytest.mark.parametrize("proc", ["print", "report", "tabulate", "freq"])
def test_aviso_reporte_conserva_lineas(proc):
    plan = _plan(f"\nproc {proc} data=work.x;\nrun;\n")
    [notice] = [n for n in plan.not_migrated if f"PROC {proc.upper()}" in n.what]
    assert "A-REPORTE-OMITIDO" in notice.what
    assert notice.evidence[0].line_start == 2
    assert notice.evidence[0].line_end == 3
    assert not any(g.reason == "REPORTE" for g in plan.gaps)


@pytest.mark.parametrize("policy", ["discard", "log", "csv"])
@pytest.mark.parametrize(
    "statement", ["ods output Summary=work.stats;", "ODS OUTPUT 'Table.Name'n = work.result;"]
)
def test_ods_output_dataset_nunca_se_omite(policy, statement):
    plan = _plan(f"\n{statement}\n", policy)
    ops = [
        o for o in plan.graph.operators() if o.params.get("pending_code") == "P-ODS-OUTPUT-DATASET"
    ]
    assert len(ops) == 1
    assert not ops[0].params.get("outputs")
    assert any("P-ODS-OUTPUT-DATASET" in note for note in ops[0].notes)
    assert ops[0].evidence[0].line_start == 2
    assert any("ODS" in gap.text.upper() for gap in plan.gaps)
    assert not plan.not_migrated


@pytest.mark.parametrize(
    "statement",
    [
        "ods html file='a=b.html';",
        "ods listing close;",
        "ods select none;",
        "ods output close;",
        "title 'Resumen';",
        "footnote 'Fin';",
    ],
)
def test_presentacion_se_registra_sin_inventar_dataset(statement):
    plan = _plan(statement)
    assert not plan.gaps
    assert plan.not_migrated


def test_ods_desconocido_pendiente_y_options_conserva_deuda_mg_p7_07():
    plan = _plan("ods desconocido; options yearcutoff=1920;")
    assert any(g.reason == "SENTENCIA_NO_SOPORTADA" for g in plan.gaps)
    assert not any("OPTIONS" in n.what.upper() for n in plan.not_migrated)
    [option] = [o for o in plan.graph.operators() if o.params.get("reason") == "CONFIGURACION"]
    assert option.params["statement"] == "yearcutoff=1920"
    # Deuda MG-P7-07: CONFIGURACION/reemplazado todavía no publica aviso ni pendiente de la opción.
    assert option.status == "reemplazado"
    assert not option.params.get("pending_code")
    assert not any("yearcutoff" in gap.text.lower() for gap in plan.gaps)


def test_tabulate_lowering_preexistente_sigue_como_reporte():
    plan = _plan("proc tabulate data=x; var amount; table amount; run;", "log")
    assert any(g.reason == "REPORTE" for g in plan.gaps)
    assert not any(o.kind in {"report", "write_file"} for o in plan.graph.operators())


def test_ods_output_sin_asignacion_no_deduce_dataset_desde_literal():
    plan = _plan("ods output 'Table=Name';")
    assert plan.gaps
    assert not any(
        o.params.get("pending_code") == "P-ODS-OUTPUT-DATASET" for o in plan.graph.operators()
    )


def test_ods_output_publica_pendiente_especifico_en_migracion(tmp_path):
    source = tmp_path / "p.sas"
    source.write_text("\nods output Summary=work.stats;\n", encoding="utf-8")
    result = migrar(source, tmp_path / "out")
    assert any(p.codigo == "P-ODS-OUTPUT-DATASET" for p in result.pendientes)
    assert "P-ODS-OUTPUT-DATASET" in (result.carpeta / "pendientes.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("procedure", ["print", "report", "tabulate", "freq", "means"])
def test_ods_output_dentro_de_proc_no_desaparece_con_discard(procedure):
    plan = _plan(f"proc {procedure} data=x;\nods output Summary=work.stats;\nrun;")
    assert any(
        o.params.get("pending_code") == "P-ODS-OUTPUT-DATASET" for o in plan.graph.operators()
    )
    assert not plan.not_migrated


@pytest.mark.parametrize(
    "block",
    [
        "proc sql; ods output SQL_Results=work.stats; select x from a; quit;",
        "data y; ods output Objects=work.stats; set x; run;",
    ],
)
def test_ods_output_en_bloque_conserva_pendiente_sin_salida_supuesta(block):
    plan = _plan(block)
    assert any(
        o.params.get("pending_code") == "P-ODS-OUTPUT-DATASET" for o in plan.graph.operators()
    )
    assert not any(o.kind == "write" for o in plan.graph.operators())
    assert any("ods output" in gap.text.lower() for gap in plan.gaps)
