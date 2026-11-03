"""Pruebas del hito 9: decisiones por firma y alcance, persistencia e inventario de huecos."""

import pytest

from sgm.compile import compile_project
from sgm.store import gaps as gap_store
from sgm.store import overrides as override_store
from sgm.store.db import Store

MERGE = "data j; merge a(in=ina) b(in=inb); by k; if ina and inb; run;\n"


@pytest.fixture
def store(tmp_path):
    with Store(tmp_path / "sgm.sqlite") as s:
        yield s


def _compile(files: dict[str, str], store=None):
    """Compila; con `store`, repite la compilación si una decisión deja un join suelto (CLI)."""
    compiled, _ = compile_project(files)
    if store is not None:
        sueltos = override_store.joins_sueltos(store, compiled)
        if sueltos:
            compiled, _ = compile_project(files, no_fusionar=sueltos)
    return compiled


def _join_signature(compiled, program: str) -> str:
    """Firma del join: el operador suelto, o el paso de join dentro del tMap fundido."""
    for op in compiled[program].plan.graph.operators():
        if op.kind == "join":
            return op.signature
        for step in op.params.get("steps", []):
            if step.get("kind") == "join":
                return step["signature"]
    raise AssertionError("sin join")


def _component(compiled, program: str) -> str:
    for op in compiled[program].plan.graph.operators():
        if op.kind == "join" or any(s.get("kind") == "join" for s in op.params.get("steps", [])):
            return op.component["name"]
    raise AssertionError("sin join")


def test_override_global_cambia_la_salida_de_todos_los_archivos_con_esa_firma(store):
    firma = _join_signature(_compile({"a.sas": MERGE, "b.sas": MERGE}), "a.sas")
    override_store.set_override(store, firma, "tJoin", scope="global", reason="prueba")
    compiled = _compile({"a.sas": MERGE, "b.sas": MERGE}, store)
    for result in compiled.values():
        override_store.apply(result.plan, store, "proyecto")
    assert _component(compiled, "a.sas") == "tJoin"
    assert _component(compiled, "b.sas") == "tJoin"


def test_override_de_archivo_gana_sobre_el_global(store):
    firma = _join_signature(_compile({"a.sas": MERGE, "b.sas": MERGE}), "a.sas")
    override_store.set_override(store, firma, "tJoin", scope="global")
    override_store.set_override(store, firma, "tMap", scope="archivo", ref="a.sas")
    compiled = _compile({"a.sas": MERGE, "b.sas": MERGE}, store)
    for result in compiled.values():
        override_store.apply(result.plan, store, "proyecto")
    assert _component(compiled, "a.sas") == "tMap"
    assert _component(compiled, "b.sas") == "tJoin"


def test_override_sobrevive_a_una_recompilacion(store):
    firma = _join_signature(_compile({"a.sas": MERGE}), "a.sas")
    override_store.set_override(store, firma, "tJoin", scope="proyecto", ref="proyecto")
    again = _compile({"a.sas": MERGE}, store)
    assert _join_signature(again, "a.sas") == firma
    override_store.apply(again["a.sas"].plan, store, "proyecto")
    assert _component(again, "a.sas") == "tJoin"


def test_alcance_sin_referencia_o_desconocido_se_rechaza(store):
    with pytest.raises(ValueError):
        override_store.set_override(store, "f", "tJoin", scope="paso")
    with pytest.raises(ValueError):
        override_store.set_override(store, "f", "tJoin", scope="universo")


def test_inventario_de_huecos_ordena_por_archivos_y_ocurrencias(store):
    compiled = _compile(
        {
            "a.sas": "data x; set s; z = fn_una(y); run;\n",
            "b.sas": "data x; set s; z = fn_una(y); run;\n",
            "c.sas": "data x; set s; z = fn_otra(y); z = fn_otra(y); z = fn_otra(y); run;\n",
        }
    )
    rows = gap_store.inventory([r.plan for r in compiled.values()])
    gap_store.save(store, rows)
    top = gap_store.top(store, 10)
    assert top and all("files" in r and "example" in r for r in top)
    assert [len(r["files"]) for r in top] == sorted((len(r["files"]) for r in top), reverse=True)
    assert len(gap_store.top(store, 1)) == 1


def test_compilar_de_nuevo_reemplaza_el_inventario_guardado(store):
    primero = _compile({"a.sas": "data x; set s; z = fn_una(y); run;\n"})
    gap_store.save(store, gap_store.inventory([r.plan for r in primero.values()]))
    segundo = _compile({"b.sas": "data x; set s; run;\n"})
    gap_store.save(store, gap_store.inventory([r.plan for r in segundo.values()]))
    assert gap_store.top(store, 10) == []


def test_cli_decisions_set_y_list_con_base_temporal(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from sgm.cli import app

    monkeypatch.setenv("SGM_DB", str(tmp_path / "cli.sqlite"))
    runner = CliRunner()
    rechazo = runner.invoke(app, ["decisions", "set", "abc", "tJoin", "--scope", "paso"])
    assert rechazo.exit_code != 0
    ok = runner.invoke(
        app,
        [
            "decisions",
            "set",
            "abc",
            "tJoin",
            "--scope",
            "proyecto",
            "--ref",
            "p",
            "--reason",
            "prueba",
        ],
    )
    assert ok.exit_code == 0, ok.output
    listado = runner.invoke(app, ["decisions", "list"])
    assert "abc" in listado.output and "tJoin" in listado.output


def test_cli_compile_guarda_el_inventario_de_huecos(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from sgm.cli import app

    monkeypatch.setenv("SGM_DB", str(tmp_path / "cli.sqlite"))
    fuente = tmp_path / "src"
    fuente.mkdir()
    (fuente / "a.sas").write_text("data x; set s; z = fn_una(y); run;\n", encoding="utf-8")
    salida = tmp_path / "out"
    assert CliRunner().invoke(app, ["compile", str(fuente), "--out", str(salida)]).exit_code == 0
    gaps = CliRunner().invoke(app, ["gaps", "list", "--top", "5"])
    assert gaps.exit_code == 0 and "FUNCION_NO_MAPEADA" in gaps.output
