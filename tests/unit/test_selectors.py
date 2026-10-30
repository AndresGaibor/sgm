"""Selectores de ambiente: una macro con forma de elección por `&X eq <lit>` es un grupo de contexto."""

from pathlib import Path

from sgm.catalog.config import load_env
from sgm.compile import compile_project
from sgm.frontend.lexer import split_statements
from sgm.frontend.selectors import detect

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "tests" / "fixtures" / "sas" / "client"


def _body(macro: str):
    """Sentencias del cuerpo de la primera macro de `macro`."""
    stmts = split_statements(macro)
    start = next(i for i, s in enumerate(stmts) if s.text.lower().startswith("%macro"))
    end = next(i for i, s in enumerate(stmts) if s.text.lower().startswith("%mend"))
    return stmts[start + 1 : end]


SELECTOR_SINTETICO = """
%macro kx9p2;
%if &vq_amb eq A %then
%do;
/* ramo de prueba */
%let wr_dest=ALFA;
%end;
%else %if &vq_amb eq B %then
%do;
%let wr_dest=BETA;
%end;
%put &wr_dest;
%mend kx9p2;
%kx9p2;
"""


def test_detecta_selector_con_nombres_aleatorios():
    sel = detect("kx9p2", _body(SELECTOR_SINTETICO))
    assert sel is not None
    assert sel.variable == "vq_amb"
    assert sel.variables == ["wr_dest"]
    assert sel.contexts == {"A": {"wr_dest": "ALFA"}, "B": {"wr_dest": "BETA"}}


def test_con_un_solo_literal_no_hay_eleccion():
    macro = "%macro u; %if &amb eq A %then %do; %let x=1; %end; %mend u;"
    assert detect("u", _body(macro)) is None


def test_rama_sin_literal_no_es_selector():
    macro = "%macro u; %if &amb eq A %then %do; %let x=1; %end; %else %do; %let x=2; %end; %mend u;"
    assert detect("u", _body(macro)) is None


def test_variables_distintas_entre_ramas_no_es_selector():
    macro = (
        "%macro u; %if &a eq A %then %do; %let x=1; %end; "
        "%else %if &b eq B %then %do; %let x=2; %end; %mend u;"
    )
    assert detect("u", _body(macro)) is None


def test_cuerpo_con_codigo_extra_no_es_selector():
    macro = (
        "%macro u; %if &a eq A %then %do; %let x=1; %end; "
        "%else %if &a eq B %then %do; %let x=2; %end; data work.z; set work.y; run; %mend u;"
    )
    assert detect("u", _body(macro)) is None


def test_el_programa_con_selector_no_genera_operadores_de_las_ramas():
    compiled, _ = compile_project({"p.sas": SELECTOR_SINTETICO})
    plan = compiled["p.sas"].plan
    assert len(plan.graph) == 0
    group = plan.jobs[0].context_groups["kx9p2"]
    assert group["selector"] == "vq_amb"
    assert group["contextos"]["B"] == {"wr_dest": "BETA"}


def test_el_selector_real_del_cliente_da_el_grupo_lz_dsn():
    env = load_env(ROOT / "env")
    text = (CLIENT / "client_poc.sas").read_text(encoding="utf-8", errors="replace")
    compiled, _ = compile_project({"client_poc.sas": text}, env=env)
    group = compiled["client_poc.sas"].plan.jobs[0].context_groups["ambiente"]
    assert group["selector"] == "m_ambiente"
    assert group["variables"] == ["lz_dsn"]
    assert group["contextos"] == {
        "D": {"lz_dsn": "IMPALA"},
        "C": {"lz_dsn": "IMPALAC"},
        "P": {"lz_dsn": "IMPALAP"},
    }
