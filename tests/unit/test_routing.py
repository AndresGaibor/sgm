"""Ruteo de huecos (F1.5): `rules/routing.yaml` es la fuente de dueños, y `gaps list` filtra por ellos."""

from sgm import motivos
from sgm.compile import compile_project
from sgm.store import gaps as gap_store
from sgm.store.db import Store

DUENOS = {"joseph", "byron", "andres"}


def test_todo_motivo_tiene_dueño_valido_y_arreglo():
    for motivo in motivos.HUECOS:
        assert motivo.dueño in DUENOS, motivo.codigo
        assert motivo.se_cierra_con, motivo.codigo


def test_motivos_fuera_del_contrato_salen_de_routing():
    pendientes = {m.codigo for m in motivos.HUECOS if not m.contrato}
    assert pendientes == {"COMANDO_SISTEMA", "MACRO_NO_EXPANDIDA", "SQL_NO_SOPORTADO"}


def _store_con_huecos(tmp_path):
    compiled, _ = compile_project(
        {
            "a.sas": "data x; set s; z = zzfuncionfalsa(y); run;\n",
            "b.sas": 'data x; set s; z = zzfuncionfalsa(y); run;\n%include "otro.sas";\n',
        }
    )
    store = Store(tmp_path / "huecos.db")
    gap_store.save(store, gap_store.inventory([r.plan for r in compiled.values()]))
    return store


def test_filtro_por_dueño(tmp_path):
    store = _store_con_huecos(tmp_path)
    try:
        byron = gap_store.top(store, 50, owner="byron")
        assert byron and {r["reason"] for r in byron} <= {"TIPO_DESCONOCIDO", "INCLUDE_EXTERNO"}
        assert all(r["owner"] == "byron" for r in byron)
        assert {r["reason"] for r in gap_store.top(store, 50, owner="joseph")} == {
            "FUNCION_NO_MAPEADA"
        }
    finally:
        store.close()


def test_filtro_por_archivo(tmp_path):
    store = _store_con_huecos(tmp_path)
    try:
        solo_b = gap_store.top(store, 50, file="b.sas")
        assert solo_b and all(any("b.sas" in f for f in r["files"]) for r in solo_b)
        assert any(r["reason"] == "INCLUDE_EXTERNO" for r in solo_b)
    finally:
        store.close()


def test_el_comando_sugerido_usa_el_tipo_de_regla(tmp_path):
    store = _store_con_huecos(tmp_path)
    try:
        rows = {r["reason"]: r for r in gap_store.top(store, 50)}
        assert rows["FUNCION_NO_MAPEADA"]["comando"].startswith(
            "sgm rules new function --from-gap "
        )
        assert rows["INCLUDE_EXTERNO"]["comando"].startswith("sgm case new --from-gap ")
    finally:
        store.close()
