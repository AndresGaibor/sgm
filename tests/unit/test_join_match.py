"""Modelo de coincidencia y tipo de unión de los joins que van a un tMap (tareas 20 a 22)."""

import pytest

from sgm.compile import compile_project
from sgm.ir.models import Operator
from sgm.ir.signature import signature
from sgm.passes import join_match


def _joins(text: str) -> list[Operator]:
    """Joins del programa. Desde la pasada 6, un join suele quedar dentro de un `map` fundido:
    en ese caso se devuelve una vista con el mismo componente (`match_model`, `join_type`)."""
    from types import SimpleNamespace

    compiled, _ = compile_project({"p.sas": text})
    vistas = []
    for o in compiled["p.sas"].plan.graph.operators():
        if o.kind == "join":
            vistas.append(o)
        elif o.kind == "map" and any(st.get("kind") == "join" for st in o.params.get("steps", [])):
            joins = (o.component or {}).get("joins", [])
            comp = dict(o.component or {})
            if joins:
                comp["match_model"] = joins[0]["match_model"]
                comp["join_type"] = joins[0]["join_type"]
            paso = next(
                st for st in o.params.get("steps", []) if st.get("kind") == "join"
            )
            vistas.append(SimpleNamespace(kind="join", component=comp, notes=o.notes,
                                          params=dict(paso.get("params", {})),
                                          signature=paso.get("signature", o.signature), id=o.id))
    return vistas


def _sql_join(kind: str) -> str:
    return (
        "proc sql;\n"
        f" create table t as select a.k, b.v from s a {kind} join r b on a.k = b.k;\n"
        "quit;\n"
    )


def _join_op(
    text: str = "proc sql; create table t as select a.k from s a join r b on a.k = b.k; quit;",
):
    (op,) = _joins(text)
    return op


def test_join_sql_inner_queda_en_tmap_con_modelo_all_e_inner():
    (op,) = _joins(_sql_join(""))
    assert op.component["name"] == "tMap"
    assert op.component["match_model"] == "all"
    assert op.component["join_type"] == "inner"


def test_join_sql_left_queda_con_tipo_left_outer():
    (op,) = _joins(_sql_join("left"))
    assert op.component["join_type"] == "left outer"


def test_join_sql_right_no_tiene_tipo_tmap_y_lo_advierte():
    (op,) = _joins(_sql_join("right"))
    assert op.component["join_type"] is None
    assert any("tipo de unión right" in note for note in op.notes)


def test_join_sql_no_lleva_advertencia_de_modelo():
    (op,) = _joins(_sql_join(""))
    assert not any("suposición" in note or "unique match" in note for note in op.notes)


def test_merge_con_if_and_queda_con_modelo_all_como_suposicion_advertida():
    (op,) = _joins("data j; merge a(in=ina) b(in=inb); by id; if ina and inb; run;")
    assert op.component["match_model"] == "all"
    assert op.component["join_type"] == "inner"
    assert any(note.startswith("MERGE:") for note in op.notes)


def test_describe_unique_advierte_que_conserva_la_ultima_fila():
    info = join_match.describe(_join_op(), model="unique")
    assert info["match_model"] == "unique"
    assert any("última fila coincidente" in note for note in info["notes"])


def test_describe_first_advierte_que_conserva_la_primera_fila():
    info = join_match.describe(_join_op(), model="first")
    assert info["match_model"] == "first"
    assert any("primera fila coincidente" in note for note in info["notes"])


def test_describe_all_no_advierte_del_modelo():
    info = join_match.describe(_join_op(), model="all")
    assert info["match_model"] == "all"
    assert info["notes"] == []


def test_describe_rechaza_un_modelo_desconocido():
    with pytest.raises(ValueError, match="desconocido"):
        join_match.describe(_join_op(), model="cualquiera")


def test_attach_no_repite_advertencias_al_ejecutarse_dos_veces():
    op = _join_op()
    op.params["join_type"] = "right"
    component: dict = {"name": "tMap"}
    join_match.attach(op, component)
    count = len(op.notes)
    join_match.attach(op, component)
    assert len(op.notes) == count


def test_la_firma_del_join_no_cambia_al_anadir_el_modelo():
    op = _join_op()
    assert op.signature == signature("join", op.params)
    assert "match_model" not in op.params and "match_model" not in op.signature
