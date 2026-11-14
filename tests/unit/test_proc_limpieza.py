"""Limpiezas de WORK y copias de PROC con límites explícitos."""

from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.frontend.program import analyze_program
from sgm.ir.lower import lower_items
from sgm.ir.models import Plan
from sgm.passes.base import PassContext
from sgm.passes.p02_plumbing import mark


def _plan(text: str) -> Plan:
    plan = Plan(program="p.sas")
    lower_items(analyze_program({"p.sas": text}).items, plan.graph)
    return plan


def test_proc_delete_de_work_se_marca_como_limpieza_y_deja_aviso():
    plan = _plan("proc delete data=work.tmp; run;")

    (operator,) = plan.graph.operators()
    assert operator.kind == "unsupported"
    assert operator.params["reason"] == "LIMPIEZA"
    assert any("A-PROC-LIMPIEZA-OMITIDO" in note for note in operator.notes)

    log = mark(plan.graph, PassContext(plan=plan))

    assert len(plan.not_migrated) == 1
    assert "A-PROC-LIMPIEZA-OMITIDO" in plan.not_migrated[0].what
    assert log.metrics == {"omisiones_work": 1}


def test_proc_delete_persistente_queda_con_codigo_especifico():
    plan = _plan("proc delete data=lz.tmp; run;")

    (operator,) = plan.graph.operators()
    assert operator.kind == "unsupported"
    assert operator.status == "hueco"
    assert operator.params["pending_code"] == "P-DELETE-PERSISTENTE"


def test_proc_delete_con_biblioteca_dinamica_queda_ambiguo():
    plan = _plan("proc delete data=&lib..tmp; run;")

    (operator,) = plan.graph.operators()
    assert operator.params["pending_code"] == "P-DELETE-BIBLIOTECA-SIN-DEMOSTRAR"


def test_proc_delete_con_library_persistente_queda_con_codigo_persistente():
    plan = _plan("proc delete library=lz data=tmp; run;")

    (operator,) = plan.graph.operators()
    assert operator.params["pending_code"] == "P-DELETE-PERSISTENTE"


def test_proc_datasets_solo_omite_delete_con_library_work_explicita():
    plan = _plan("proc datasets library=work nolist; delete tmp; quit;")

    (operator,) = plan.graph.operators()
    assert operator.params["reason"] == "LIMPIEZA"


def test_proc_datasets_sin_biblioteca_queda_pendiente_por_defecto_no_demostrado():
    plan = _plan("proc datasets nolist; delete tmp; quit;")

    (operator,) = plan.graph.operators()
    assert operator.params["pending_code"] == "P-DELETE-BIBLIOTECA-SIN-DEMOSTRAR"


def test_proc_datasets_con_library_persistente_queda_pendiente():
    plan = _plan("proc datasets library=lz; delete tmp; quit;")

    (operator,) = plan.graph.operators()
    assert operator.params["pending_code"] == "P-DELETE-PERSISTENTE"


def test_proc_contents_de_work_sin_out_se_omite_como_diagnostico():
    plan = _plan("proc contents data=work.tmp; run;")

    (operator,) = plan.graph.operators()
    assert operator.params["reason"] == "REPORTE"

    mark(plan.graph, PassContext(plan=plan))

    assert "A-PROC-LIMPIEZA-OMITIDO" in plan.not_migrated[0].what


def test_proc_copy_sin_select_queda_pendiente():
    plan = _plan("proc copy in=origen out=work; run;")

    (operator,) = plan.graph.operators()
    assert operator.kind == "unsupported"
    assert operator.params["pending_code"] == "P-COPY-SIN-LISTA"


def test_proc_copy_a_biblioteca_persistente_queda_pendiente():
    plan = _plan("proc copy in=origen out=clientes; select ventas; run;")

    (operator,) = plan.graph.operators()
    assert operator.kind == "unsupported"
    assert operator.params["pending_code"] == "P-COPY-PERSISTENTE"


def test_proc_copy_a_la_misma_biblioteca_queda_pendiente():
    plan = _plan("proc copy in=work out=work; select ventas; run;")

    (operator,) = plan.graph.operators()
    assert operator.kind == "unsupported"
    assert operator.params["pending_code"] == "P-COPY-MISMA-BIBLIOTECA"


def test_proc_copy_a_work_crea_lectura_y_escritura_por_tabla_seleccionada():
    plan = _plan("proc copy in=origen out=work; select ventas compras; run;")

    assert [operator.kind for operator in plan.graph.operators()] == [
        "read",
        "write",
        "read",
        "write",
    ]
    assert [operator.params["dataset"] for operator in plan.graph.operators()] == [
        "ORIGEN.ventas",
        "WORK.ventas",
        "ORIGEN.compras",
        "WORK.compras",
    ]


def test_caso_l6_limpieza_work_migra_sin_huecos_y_con_tres_avisos(tmp_path: Path):
    case = Path(__file__).resolve().parents[1] / "corpus" / "L6" / "l6_63_limpieza_work"
    source = case / "programa.sas"
    plan = _plan(source.read_text(encoding="utf-8"))
    mark(plan.graph, PassContext(plan=plan))

    avisos = [item.what for item in plan.not_migrated if "A-PROC-LIMPIEZA-OMITIDO" in item.what]
    assert len(avisos) == 3
    assert not any("ventas2" in aviso for aviso in avisos)

    result = migrar(source, tmp_path / "out", muestra=case / "entradas")

    assert result.jobs
    assert result.pendientes == [], result.pendientes
    assert result.fallo_seguridad is None
