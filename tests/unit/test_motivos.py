"""Motivos de hueco (F1.1): todo motivo emitido está registrado y ningún operador queda sin estado."""

from pathlib import Path

from sgm import motivos
from sgm.batch import compile_batch
from sgm.cli import _collect
from sgm.ir.models import STATUSES

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sas"


def _compiled():
    files = {k: v for k, v in _collect(FIXTURES / "client").items()}
    files.update({"p0.sas": (FIXTURES / "p0_ejemplo_basico.sas").read_text(encoding="utf-8")})
    compiled, _ = compile_batch(files, workers=1)
    return compiled


def test_todo_motivo_emitido_esta_registrado():
    usados = {gap.reason for result in _compiled().values() for gap in result.plan.gaps}
    assert motivos.sin_registrar(usados) == set()


def test_ningun_operador_queda_sin_estado():
    for result in _compiled().values():
        assert all(op.status in STATUSES for op in result.plan.graph.operators())


def test_el_registro_incluye_los_tres_motivos_de_la_fase_1():
    codigos = {m.codigo for m in motivos.HUECOS}
    assert {"INCLUDE_EXTERNO", "COMPONENTE_NO_CATALOGADO", "INTRINSECO_PARCIAL"} <= codigos


def test_los_motivos_fuera_del_contrato_se_marcan():
    fuera = {m.codigo for m in motivos.HUECOS if not m.contrato}
    assert fuera == {"COMANDO_SISTEMA", "MACRO_NO_EXPANDIDA", "SQL_NO_SOPORTADO"}


def test_un_componente_fuera_del_catalogo_es_hueco():
    from sgm.compile import _catalog_and_intrinsic_gaps
    from sgm.ir.models import Graph, Operator

    graph = Graph()
    graph.add_operator(Operator(id="op1", kind="filter", component={"name": "tInventado"}))
    gaps = _catalog_and_intrinsic_gaps(graph)
    assert [g.reason for g in gaps] == ["COMPONENTE_NO_CATALOGADO"]


def test_una_carga_de_region_parcial_es_intrinseco_parcial():
    from sgm.compile import _catalog_and_intrinsic_gaps
    from sgm.ir.models import Graph, Operator

    graph = Graph()
    graph.add_operator(
        Operator(
            id="op1",
            kind="external_load",
            status="parcial",
            params={"absorbed": 3},
            signature="s",
            component={"name": "tImpalaOutput"},
        )
    )
    assert [g.reason for g in _catalog_and_intrinsic_gaps(graph)] == ["INTRINSECO_PARCIAL"]
